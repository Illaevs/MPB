"""
Authentication endpoints.
"""
from __future__ import annotations

import uuid
import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.core.request_utils import client_ip
from app.core.security import (
    TokenExpiredError,
    create_access_token,
    create_refresh_token,
    create_two_factor_challenge_token,
    decode_token,
    is_token_type,
    token_timestamp,
    verify_password,
)
from app.database.session import get_db
from app.models import EventLog, Role, RolePermission, User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    SessionResponse,
    TokenResponse,
    TwoFactorBackupCodesResponse,
    TwoFactorDisableRequest,
    TwoFactorRegenerateBackupCodesRequest,
    TwoFactorSetupConfirmRequest,
    TwoFactorSetupStartResponse,
    TwoFactorStatusResponse,
    TwoFactorVerifyRequest,
)
from app.services.two_factor import (
    build_otpauth_uri,
    count_backup_codes,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_backup_codes,
    generate_totp_secret,
    hash_backup_codes,
    verify_and_consume_backup_code,
    verify_totp_code,
)
from app.services.auth_security_store import (
    blacklist_token_jti,
    clear_login_failures,
    clear_two_factor_challenge,
    get_two_factor_challenge_state,
    get_user_revoked_after,
    is_token_blacklisted,
    login_rate_limit_retry_after,
    mark_login_failure,
    mark_two_factor_challenge_failure,
    register_two_factor_challenge,
)
from app.services.event_outbox import emit_event_safe

router = APIRouter()

_TWO_FACTOR_MAX_ATTEMPTS = 5
_LOGIN_RATE_LIMIT_ATTEMPTS = 5
_LOGIN_RATE_LIMIT_WINDOW_SECONDS = 15 * 60


def _superuser_flag(role: Optional[Role]) -> bool:
    return bool(role and role.is_system)


async def _permissions_map(db: AsyncSession, role_id: Optional[str]) -> Dict[str, Dict[str, bool]]:
    if not role_id:
        return {}
    role = await Role.get_by_id(db, role_id)
    if _superuser_flag(role):
        return {"__superuser__": {
            "read_all": True, "read_assigned": True,
            "edit_all": True, "edit_assigned": True,
        }}
    result = await db.execute(select(RolePermission).where(RolePermission.role_id == str(role_id)))
    perms = {}
    for p in result.scalars().all():
        edit_all = bool(getattr(p, "edit_all", False))
        edit_assigned = bool(getattr(p, "edit_assigned", False))
        perms[p.section] = {
            # Implication: edit implies the matching read.
            "read_all": bool(p.read_all) or edit_all,
            "read_assigned": bool(p.read_assigned) or edit_assigned,
            "edit_all": edit_all,
            "edit_assigned": edit_assigned,
        }
    return perms


def _cookie_secure(request: Optional[Request]) -> bool:
    if request and request.url.scheme == "http" and request.client and request.client.host in {"127.0.0.1", "localhost"}:
        return False
    return bool(settings.AUTH_COOKIE_SECURE)


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    request: Optional[Request] = None,
) -> None:
    secure = _cookie_secure(request)
    common = {
        "httponly": True,
        "secure": secure,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "domain": settings.AUTH_COOKIE_DOMAIN,
    }
    response.set_cookie(
        settings.ACCESS_COOKIE_NAME,
        access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path=settings.ACCESS_COOKIE_PATH,
        **common,
    )
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path=settings.REFRESH_COOKIE_PATH,
        **common,
    )
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=secure,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path=settings.CSRF_COOKIE_PATH,
    )


def _clear_auth_cookies(response: Response) -> None:
    common = {"domain": settings.AUTH_COOKIE_DOMAIN}
    response.delete_cookie(settings.ACCESS_COOKIE_NAME, path=settings.ACCESS_COOKIE_PATH, **common)
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH, **common)
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path=settings.CSRF_COOKIE_PATH, **common)


async def _build_session_response(
    user: User,
    role: Optional[Role],
    db: AsyncSession,
) -> SessionResponse:
    # Transient (non-column) attribute — picked up by UserResponse
    # (from_attributes). Lets the frontend show the role name without
    # an extra roles fetch (which is permission-gated for non-admins).
    try:
        user.role_name = role.name if role else None
    except Exception:
        pass
    return SessionResponse(
        user=user,
        permissions=await _permissions_map(db, user.role_id),
        is_superuser=_superuser_flag(role),
    )


async def _emit_login_event(
    db: AsyncSession,
    user: User,
    *,
    flow: str,
    request: Optional[Request] = None,
) -> None:
    """Эмитим `user.after_login` после успешной выдачи токенов.
    `flow` — web/web_2fa/mobile/mobile_2fa, нужно для аналитики BI.
    Намеренно не эмитим на /refresh — это технологический хук, не login."""
    await emit_event_safe(
        db,
        event_type="user.after_login",
        entity_type="user",
        entity_id=str(user.id),
        payload={
            "id": str(user.id),
            "email": user.email,
            "role_id": str(user.role_id) if user.role_id else None,
            "flow": flow,
            "ip": client_ip(request) if request else None,
            "two_factor_used": flow.endswith("2fa"),
        },
        payload_version=1,
    )


async def _issue_tokens(
    user: User,
    role: Optional[Role],
    db: AsyncSession,
    *,
    two_factor_enabled: Optional[bool] = None,
    two_factor_verified: Optional[bool] = None,
) -> Tuple[SessionResponse, str, str]:
    effective_two_factor_enabled = bool(user.two_factor_enabled) if two_factor_enabled is None else bool(two_factor_enabled)
    effective_two_factor_verified = (
        effective_two_factor_enabled if two_factor_verified is None else bool(two_factor_verified)
    )
    payload = {
        "sub": str(user.id),
        "role_id": str(user.role_id) if user.role_id else None,
        "email": user.email,
        "two_factor_enabled": effective_two_factor_enabled,
        "two_factor_verified": effective_two_factor_verified,
    }
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return (
        await _build_session_response(user, role, db),
        access_token,
        refresh_token,
    )


def _login_response_with_tokens(
    session_response: SessionResponse,
    access_token: str,
    refresh_token: str,
    *,
    requires_two_factor_setup: bool,
) -> LoginResponse:
    payload = session_response.model_dump()
    return LoginResponse(
        **payload,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        requires_2fa=False,
        requires_2fa_setup=requires_two_factor_setup,
        challenge_token=None,
    )


def _token_response_with_tokens(
    session_response: SessionResponse,
    access_token: str,
    refresh_token: str,
) -> TokenResponse:
    payload = session_response.model_dump()
    return TokenResponse(
        **payload,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def _ensure_token_not_revoked(payload: Dict[str, object]) -> None:
    if await is_token_blacklisted(payload.get("jti")):
        raise HTTPException(status_code=401, detail="Токен был отозван.")

    user_id = payload.get("sub")
    revoked_after = await get_user_revoked_after(str(user_id)) if user_id else None
    issued_at = token_timestamp(payload, "iat")
    if revoked_after and issued_at and issued_at <= revoked_after:
        raise HTTPException(status_code=401, detail="Сессия была отозвана. Войдите снова.")


async def _blacklist_token_payload(payload: Optional[Dict[str, object]]) -> None:
    if not payload:
        return
    jti = payload.get("jti")
    expires_at = token_timestamp(payload, "exp")
    if jti and expires_at:
        await blacklist_token_jti(str(jti), expires_at)


def _status_payload(user: User) -> TwoFactorStatusResponse:
    return TwoFactorStatusResponse(
        enabled=bool(user.two_factor_enabled),
        enabled_at=user.two_factor_enabled_at,
        backup_codes_remaining=count_backup_codes(user.two_factor_backup_codes_hash),
    )


def _login_rate_key(request: Request, email: str) -> str:
    host = client_ip(request) or "unknown"
    return f"{host}:{(email or '').strip().lower()}"


async def _check_login_rate_limit_redis(key: str) -> None:
    retry_after = await login_rate_limit_retry_after(key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail=f"РЎР»РёС€РєРѕРј РјРЅРѕРіРѕ РїРѕРїС‹С‚РѕРє РІС…РѕРґР°. РџРѕРІС‚РѕСЂРёС‚Рµ С‡РµСЂРµР· {retry_after} СЃРµРє.",
        )


async def _mark_login_failure_redis(key: str) -> None:
    await mark_login_failure(key, _LOGIN_RATE_LIMIT_ATTEMPTS, _LOGIN_RATE_LIMIT_WINDOW_SECONDS)


async def _clear_login_failures_redis(key: str) -> None:
    await clear_login_failures(key)


async def _register_challenge_redis(challenge_id: str) -> None:
    await register_two_factor_challenge(
        challenge_id,
        settings.TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES * 60,
    )


async def _ensure_challenge_state_redis(challenge_id: str) -> Dict[str, float]:
    state = await get_two_factor_challenge_state(challenge_id)
    if not state:
        raise HTTPException(status_code=401, detail="РЎСЂРѕРє РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA РёСЃС‚РµРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.")
    if state.get("attempts", 0) >= _TWO_FACTOR_MAX_ATTEMPTS:
        await clear_two_factor_challenge(challenge_id)
        raise HTTPException(status_code=429, detail="РџСЂРµРІС‹С€РµРЅРѕ С‡РёСЃР»Рѕ РїРѕРїС‹С‚РѕРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.")
    return state


async def _mark_challenge_failure_redis(challenge_id: str) -> None:
    await mark_two_factor_challenge_failure(challenge_id)


async def _clear_challenge_redis(challenge_id: str) -> None:
    await clear_two_factor_challenge(challenge_id)


async def _load_login_user(db: AsyncSession, email: str, password: str, *, rate_key: str) -> tuple[User, Optional[Role]]:
    user = await User.get_by_email(db, email)
    # Password hashing (pbkdf2/bcrypt) is CPU-bound — offload so it does
    # not block the event loop under a login burst.
    password_ok = bool(user) and await run_in_threadpool(
        verify_password, password, user.password_hash
    )
    if not password_ok:
        await _mark_login_failure_redis(rate_key)
        raise HTTPException(status_code=401, detail="Неверный email или пароль.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь отключен.")
    await _clear_login_failures_redis(rate_key)
    role = await Role.get_by_id(db, user.role_id) if user.role_id else None
    return user, role


async def _ensure_login_two_factor_state(user: User, db: AsyncSession) -> bool:
    if not settings.REQUIRE_TWO_FACTOR:
        return False
    if not user.two_factor_enabled:
        return False
    secret = decrypt_totp_secret(user.two_factor_secret_enc)
    if secret:
        return True
    user.two_factor_enabled = False
    user.two_factor_secret_enc = None
    user.two_factor_backup_codes_hash = None
    user.two_factor_enabled_at = None
    await db.commit()
    await db.refresh(user)
    return False


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    rate_key = _login_rate_key(request, payload.email)
    await _check_login_rate_limit_redis(rate_key)
    user, role = await _load_login_user(db, payload.email, payload.password, rate_key=rate_key)
    if await _ensure_login_two_factor_state(user, db):
        challenge_id = uuid.uuid4().hex
        await _register_challenge_redis(challenge_id)
        challenge_token = create_two_factor_challenge_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "cid": challenge_id,
                "is_superuser": _superuser_flag(role),
            }
        )
        return LoginResponse(
            requires_2fa=True,
            requires_2fa_setup=False,
            challenge_token=challenge_token,
            is_superuser=_superuser_flag(role),
        )

    token_response = await _issue_tokens(
        user,
        role,
        db,
        two_factor_enabled=bool(user.two_factor_enabled) if settings.REQUIRE_TWO_FACTOR else False,
        two_factor_verified=False if settings.REQUIRE_TWO_FACTOR else False,
    )
    session_response, access_token, refresh_token = token_response
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token, request=request)
    await _emit_login_event(db, user, flow="web", request=request)
    return LoginResponse(
        **session_response.model_dump(),
        requires_2fa=False,
        requires_2fa_setup=bool(settings.REQUIRE_TWO_FACTOR),
        challenge_token=None,
    )


@router.post("/verify-2fa", response_model=SessionResponse)
async def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        token_data = decode_token(payload.challenge_token)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Срок подтверждения 2FA истек. Войдите заново.")
    except Exception:
        raise HTTPException(status_code=401, detail="Недействительный токен подтверждения 2FA.")
    if not is_token_type(token_data, "2fa_challenge"):
        raise HTTPException(status_code=401, detail="Недействительный тип токена.")

    challenge_id = token_data.get("cid")
    user_id = token_data.get("sub")
    if not challenge_id or not user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен подтверждения 2FA.")

    await _ensure_challenge_state_redis(challenge_id)

    user = await User.get_by_id(db, user_id)
    if not user or not user.is_active:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=401, detail="Пользователь не найден или отключен.")
    if not user.two_factor_enabled:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=400, detail="Для пользователя не настроена двухфакторная аутентификация.")

    secret = decrypt_totp_secret(user.two_factor_secret_enc)
    if not secret:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=400, detail="Секрет 2FA поврежден или отсутствует.")

    code = str(payload.code or "").strip()
    verified = verify_totp_code(secret, code)
    if not verified:
        matched, updated_hashes = verify_and_consume_backup_code(code, user.two_factor_backup_codes_hash)
        if matched:
            user.two_factor_backup_codes_hash = updated_hashes
            await db.commit()
            await db.refresh(user)
            verified = True

    if not verified:
        await _mark_challenge_failure_redis(challenge_id)
        raise HTTPException(status_code=401, detail="Неверный код 2FA или резервный код.")

    await _clear_challenge_redis(challenge_id)
    role = await Role.get_by_id(db, user.role_id) if user.role_id else None
    session_response, access_token, refresh_token = await _issue_tokens(user, role, db)
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token, request=request)
    await _emit_login_event(db, user, flow="web_2fa", request=request)
    return session_response


@router.post("/mobile/login", response_model=LoginResponse)
async def mobile_login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    rate_key = _login_rate_key(request, payload.email)
    await _check_login_rate_limit_redis(rate_key)
    user, role = await _load_login_user(db, payload.email, payload.password, rate_key=rate_key)
    if await _ensure_login_two_factor_state(user, db):
        challenge_id = uuid.uuid4().hex
        await _register_challenge_redis(challenge_id)
        challenge_token = create_two_factor_challenge_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "cid": challenge_id,
                "is_superuser": _superuser_flag(role),
            }
        )
        return LoginResponse(
            requires_2fa=True,
            requires_2fa_setup=False,
            challenge_token=challenge_token,
            is_superuser=_superuser_flag(role),
        )

    session_response, access_token, refresh_token = await _issue_tokens(
        user,
        role,
        db,
        two_factor_enabled=bool(user.two_factor_enabled) if settings.REQUIRE_TWO_FACTOR else False,
        two_factor_verified=False if settings.REQUIRE_TWO_FACTOR else False,
    )
    await _emit_login_event(db, user, flow="mobile", request=request)
    return _login_response_with_tokens(
        session_response,
        access_token,
        refresh_token,
        requires_two_factor_setup=bool(settings.REQUIRE_TWO_FACTOR),
    )


@router.post("/mobile/verify-2fa", response_model=TokenResponse)
async def mobile_verify_two_factor(
    payload: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        token_data = decode_token(payload.challenge_token)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="РЎСЂРѕРє РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA РёСЃС‚РµРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.")
    except Exception:
        raise HTTPException(status_code=401, detail="РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РѕРєРµРЅ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA.")
    if not is_token_type(token_data, "2fa_challenge"):
        raise HTTPException(status_code=401, detail="РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РёРї С‚РѕРєРµРЅР°.")

    challenge_id = token_data.get("cid")
    user_id = token_data.get("sub")
    if not challenge_id or not user_id:
        raise HTTPException(status_code=401, detail="РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РѕРєРµРЅ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ 2FA.")

    await _ensure_challenge_state_redis(challenge_id)

    user = await User.get_by_id(db, user_id)
    if not user or not user.is_active:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=401, detail="РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё РѕС‚РєР»СЋС‡РµРЅ.")
    if not user.two_factor_enabled:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=400, detail="Р”Р»СЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РЅРµ РЅР°СЃС‚СЂРѕРµРЅР° РґРІСѓС…С„Р°РєС‚РѕСЂРЅР°СЏ Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ.")

    secret = decrypt_totp_secret(user.two_factor_secret_enc)
    if not secret:
        await _clear_challenge_redis(challenge_id)
        raise HTTPException(status_code=400, detail="РЎРµРєСЂРµС‚ 2FA РїРѕРІСЂРµР¶РґРµРЅ РёР»Рё РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚.")

    code = str(payload.code or "").strip()
    verified = verify_totp_code(secret, code)
    if not verified:
        matched, updated_hashes = verify_and_consume_backup_code(code, user.two_factor_backup_codes_hash)
        if matched:
            user.two_factor_backup_codes_hash = updated_hashes
            await db.commit()
            await db.refresh(user)
            verified = True

    if not verified:
        await _mark_challenge_failure_redis(challenge_id)
        raise HTTPException(status_code=401, detail="РќРµРІРµСЂРЅС‹Р№ РєРѕРґ 2FA РёР»Рё СЂРµР·РµСЂРІРЅС‹Р№ РєРѕРґ.")

    await _clear_challenge_redis(challenge_id)
    role = await Role.get_by_id(db, user.role_id) if user.role_id else None
    session_response, access_token, refresh_token = await _issue_tokens(user, role, db)
    await _emit_login_event(db, user, flow="mobile_2fa")
    return _token_response_with_tokens(session_response, access_token, refresh_token)


@router.post("/refresh", response_model=SessionResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = payload.refresh_token or request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token отсутствует.")
    try:
        token_data = decode_token(refresh_token)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Срок действия refresh token истек. Войдите заново.")
    except Exception:
        raise HTTPException(status_code=401, detail="Недействительный refresh token.")
    if not is_token_type(token_data, "refresh"):
        raise HTTPException(status_code=401, detail="Недействительный тип токена.")
    await _ensure_token_not_revoked(token_data)
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Некорректные данные токена.")
    user = await User.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден или отключен.")
    role = await Role.get_by_id(db, user.role_id) if user.role_id else None
    session_response, access_token, new_refresh_token = await _issue_tokens(user, role, db)
    await _blacklist_token_payload(token_data)
    _set_auth_cookies(response, access_token=access_token, refresh_token=new_refresh_token, request=request)
    return session_response


@router.post("/mobile/refresh", response_model=TokenResponse)
async def mobile_refresh_tokens(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = payload.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚.")
    try:
        token_data = decode_token(refresh_token)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ refresh token РёСЃС‚РµРє. Р’РѕР№РґРёС‚Рµ Р·Р°РЅРѕРІРѕ.")
    except Exception:
        raise HTTPException(status_code=401, detail="РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ refresh token.")
    if not is_token_type(token_data, "refresh"):
        raise HTTPException(status_code=401, detail="РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РёРї С‚РѕРєРµРЅР°.")
    await _ensure_token_not_revoked(token_data)
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="РќРµРєРѕСЂСЂРµРєС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ С‚РѕРєРµРЅР°.")
    user = await User.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё РѕС‚РєР»СЋС‡РµРЅ.")
    role = await Role.get_by_id(db, user.role_id) if user.role_id else None
    session_response, access_token, new_refresh_token = await _issue_tokens(user, role, db)
    await _blacklist_token_payload(token_data)
    return _token_response_with_tokens(session_response, access_token, new_refresh_token)


@router.post("/impersonate/{user_id}", response_model=SessionResponse)
async def impersonate_user(
    user_id: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    current_user: Optional[User] = getattr(request.state, "user", None)
    is_superuser: bool = bool(getattr(request.state, "is_superuser", False))
    if not current_user or not is_superuser:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")
    if not bool(getattr(request.state, "two_factor_enabled", False)) or not bool(
        getattr(request.state, "two_factor_verified", False)
    ):
        raise HTTPException(status_code=403, detail="Имперсонация доступна только после подтвержденной 2FA.")

    target = await User.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь для переключения не найден.")
    if not target.is_active:
        raise HTTPException(status_code=403, detail="Пользователь для переключения отключен.")
    if not target.two_factor_enabled:
        raise HTTPException(status_code=403, detail="Нельзя переключиться на пользователя без настроенной 2FA.")

    role = await Role.get_by_id(db, target.role_id) if target.role_id else None

    await EventLog.create(
        db,
        entity_type="auth",
        entity_id=str(target.id),
        action="impersonate",
        details=f"Impersonated by {current_user.email} ({current_user.id})",
        created_by=str(current_user.id),
    )
    session_response, access_token, refresh_token = await _issue_tokens(target, role, db)
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token, request=request)
    return session_response


@router.get("/session", response_model=SessionResponse)
async def get_session(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден или отключен.")
    role = await Role.get_by_id(db, current_user.role_id) if current_user.role_id else None
    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        response.set_cookie(
            settings.CSRF_COOKIE_NAME,
            secrets.token_urlsafe(32),
            max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            httponly=False,
            secure=_cookie_secure(request),
            samesite=settings.AUTH_COOKIE_SAMESITE,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path=settings.CSRF_COOKIE_PATH,
        )
    return await _build_session_response(current_user, role, db)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get(settings.ACCESS_COOKIE_NAME)
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    access_payload = None
    refresh_payload = None
    if access_token:
        try:
            access_payload = decode_token(access_token)
        except Exception:
            access_payload = None
    if refresh_token:
        try:
            refresh_payload = decode_token(refresh_token)
        except Exception:
            refresh_payload = None
    await _blacklist_token_payload(access_payload)
    await _blacklist_token_payload(refresh_payload)
    _clear_auth_cookies(response)
    # Emit logout event (best-effort — если токен невалиден, user_id будет None,
    # тогда событие не эмитим, чтобы не засорять каталог пустыми entity_id).
    user_id = (access_payload or refresh_payload or {}).get("sub") if (access_payload or refresh_payload) else None
    if user_id:
        await emit_event_safe(
            db,
            event_type="user.after_logout",
            entity_type="user",
            entity_id=str(user_id),
            payload={
                "id": str(user_id),
                "email": (access_payload or refresh_payload or {}).get("email"),
                "ip": client_ip(request),
            },
            payload_version=1,
        )
    return {"ok": True}


@router.get("/2fa/status", response_model=TwoFactorStatusResponse)
async def two_factor_status(
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return _status_payload(current_user)


@router.post("/2fa/setup/start", response_model=TwoFactorSetupStartResponse)
async def start_two_factor_setup(
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA уже настроена.")

    secret = generate_totp_secret()
    return TwoFactorSetupStartResponse(
        secret=secret,
        otpauth_url=build_otpauth_uri(secret, current_user.email),
        issuer=settings.TWO_FACTOR_ISSUER,
        email=current_user.email,
    )


@router.post("/2fa/setup/confirm", response_model=TwoFactorBackupCodesResponse)
async def confirm_two_factor_setup(
    payload: TwoFactorSetupConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA уже настроена.")

    if not verify_totp_code(payload.secret, payload.code):
        raise HTTPException(status_code=400, detail="Неверный код подтверждения.")

    backup_codes = generate_backup_codes()
    current_user.two_factor_enabled = True
    current_user.two_factor_secret_enc = encrypt_totp_secret(payload.secret)
    current_user.two_factor_backup_codes_hash = hash_backup_codes(backup_codes)
    current_user.two_factor_enabled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(current_user)

    return TwoFactorBackupCodesResponse(
        **_status_payload(current_user).model_dump(),
        backup_codes=backup_codes,
    )


@router.post("/2fa/disable", response_model=TwoFactorStatusResponse)
async def disable_two_factor(
    payload: TwoFactorDisableRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    raise HTTPException(status_code=403, detail="Отключение 2FA запрещено политикой безопасности.")


@router.post("/2fa/regenerate-backup-codes", response_model=TwoFactorBackupCodesResponse)
async def regenerate_backup_codes(
    payload: TwoFactorRegenerateBackupCodesRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    if not current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA не настроена.")

    secret = decrypt_totp_secret(current_user.two_factor_secret_enc)
    if not secret:
        raise HTTPException(status_code=400, detail="Секрет 2FA поврежден или отсутствует.")
    if not verify_totp_code(secret, payload.code):
        raise HTTPException(status_code=401, detail="Неверный код 2FA.")

    backup_codes = generate_backup_codes()
    current_user.two_factor_backup_codes_hash = hash_backup_codes(backup_codes)
    await db.commit()
    await db.refresh(current_user)
    return TwoFactorBackupCodesResponse(
        **_status_payload(current_user).model_dump(),
        backup_codes=backup_codes,
    )
