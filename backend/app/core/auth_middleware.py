"""
Middleware that enforces authenticated access to API routes.
"""
import secrets
from typing import Iterable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.security import decode_token, is_token_type, token_timestamp
from app.database.session import async_session
from app.models import Role, User
from app.services.auth_security_store import get_user_revoked_after, is_token_blacklisted


def _is_superuser_role(role: Optional[Role]) -> bool:
    return bool(role and role.is_system)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Blocks access to /api/v1/** except auth endpoints.
    Attaches request.state.user and request.state.is_superuser.
    """

    def __init__(
        self,
        app,
        open_paths: Optional[Iterable[str]] = None,
        open_prefixes: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.open_paths = set(open_paths or [])
        self.open_prefixes = tuple(open_prefixes or [])
        self.two_factor_setup_paths = {
            "/api/v1/auth/2fa/status",
            "/api/v1/auth/2fa/setup/start",
            "/api/v1/auth/2fa/setup/confirm",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if request.method == "OPTIONS" or not path.startswith("/api/v1"):
            return await call_next(request)

        if path in self.open_paths or any(path.startswith(prefix) for prefix in self.open_prefixes):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None
        using_bearer_token = False
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]
            using_bearer_token = True
        else:
            token = request.cookies.get(settings.ACCESS_COOKIE_NAME)

        if not token:
            return JSONResponse(status_code=401, content={"detail": "Требуется авторизация."})

        try:
            payload = decode_token(token)
            if not is_token_type(payload, "access"):
                raise ValueError("Invalid token type")
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Недействительный токен доступа."})

        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and not using_bearer_token
            and path not in settings.CSRF_EXEMPT_PATHS
        ):
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
            if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
                return JSONResponse(status_code=403, content={"detail": "CSRF-токен отсутствует или недействителен."})

        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(status_code=401, content={"detail": "Некорректные данные токена доступа."})
        if await is_token_blacklisted(payload.get("jti")):
            return JSONResponse(status_code=401, content={"detail": "Токен доступа был отозван."})

        revoked_after = await get_user_revoked_after(str(user_id))
        issued_at = token_timestamp(payload, "iat")
        if revoked_after and issued_at and issued_at <= revoked_after:
            return JSONResponse(status_code=401, content={"detail": "Текущая сессия была отозвана. Войдите снова."})

        async with async_session() as db:
            user = await User.get_by_id(db, user_id)
            if not user or not user.is_active:
                return JSONResponse(status_code=401, content={"detail": "Пользователь не найден или отключен."})
            role = await Role.get_by_id(db, user.role_id) if user.role_id else None

        request.state.user = user
        request.state.role = role
        request.state.is_superuser = _is_superuser_role(role)
        request.state.two_factor_enabled = bool(payload.get("two_factor_enabled") or getattr(user, "two_factor_enabled", False))
        request.state.two_factor_verified = bool(payload.get("two_factor_verified", False))
        if settings.REQUIRE_TWO_FACTOR and not (request.state.two_factor_enabled and request.state.two_factor_verified):
            if path not in self.two_factor_setup_paths:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Требуется обязательная настройка двухфакторной аутентификации."},
                )
        return await call_next(request)


def CurrentUser(request: Request) -> User:
    """Dependency returning the authenticated user from the auth middleware."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован.")
    return user
