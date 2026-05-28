"""
Mail (Yandex OAuth + IMAP/SMTP) endpoints.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select, delete, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, is_token_type
from app.core.config import settings
from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Mailbox, MailMessage, User
from app.schemas.mail import (
    MailboxCreate,
    MailboxResponse,
    MailboxAuthUrl,
    MailboxAppPassword,
    MailFolderResponse,
    MailMessageList,
    MailMessageMoveRequest,
    MailMessageResponse,
    MailSendRequest,
    MailSendResponse,
)
from app.services.event_outbox import emit_event_safe
from app.services.mail_smtp import MailSendAuthenticationError, MailSendTransportError, send_message
from app.services.mail_sync import ensure_valid_token, sync_mailbox
from app.services.mail_imap import fetch_message_attachment, fetch_message_body, move_message_to_folder, normalize_snippet_text
from app.services.permissions import get_section_permissions
from app.services.yandex_oauth import build_auth_url, build_state, exchange_code, verify_state

router = APIRouter()
logger = logging.getLogger(__name__)

MAIL_FOLDERS = [
    {"id": "inbox", "label": "Входящие", "icon": "inbox"},
    {"id": "important", "label": "Важные", "icon": "star"},
    {"id": "sent", "label": "Отправленные", "icon": "paper-plane"},
    {"id": "drafts", "label": "Черновики", "icon": "file-alt"},
    {"id": "archive", "label": "Архив", "icon": "archive"},
    {"id": "spam", "label": "Спам", "icon": "exclamation-circle"},
    {"id": "trash", "label": "Корзина", "icon": "trash-alt"},
]

REAL_MAIL_FOLDERS = {"inbox", "sent", "drafts", "archive", "spam", "trash"}


def _mail_auth(mailbox: Mailbox) -> tuple[str, Optional[str]]:
    if mailbox.provider == "yandex_app_password":
        return "password", mailbox.access_token or ""
    return "oauth", None


def _storage_uid(folder_key: str, uid: str) -> str:
    uid = str(uid or "")
    if folder_key == "inbox" or uid.startswith(f"{folder_key}:"):
        return uid
    return f"{folder_key}:{uid}"


def _message_imap_uid(item: MailMessage) -> str:
    folder = item.folder or "inbox"
    uid = str(item.uid or "")
    prefix = f"{folder}:"
    if uid.startswith(prefix):
        return uid[len(prefix):]
    return uid


def _message_is_read(item: MailMessage) -> bool:
    return "\\Seen" in (item.flags or "")


def _serialize_message(item: MailMessage) -> MailMessageResponse:
    return MailMessageResponse(
        id=item.id,
        mailbox_id=item.mailbox_id,
        uid=item.uid,
        folder=item.folder or "inbox",
        subject=item.subject,
        from_addr=item.from_addr,
        to_addr=item.to_addr,
        cc_addr=item.cc_addr,
        date=item.date,
        snippet=item.snippet,
        is_read=_message_is_read(item),
        has_attachments=bool(item.has_attachments),
        attachments_count=1 if item.has_attachments else 0,
    )


def _safe_attachment_media_type(value: Optional[str]) -> str:
    media_type = (value or "application/octet-stream").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*", media_type):
        return "application/octet-stream"
    return media_type


async def _user_has_mail_access(request: Optional[Request], db: AsyncSession, user: Optional[User]) -> bool:
    if not user or not user.role_id:
        return False
    if request is not None and getattr(request.state, "is_superuser", False):
        return True
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "mail")
    return bool(read_all or read_assigned)


async def _require_mail_access(request: Request, db: AsyncSession, user: User):
    if not await _user_has_mail_access(request, db, user):
        raise HTTPException(status_code=403, detail="Недостаточно прав для работы с почтой.")


async def _get_callback_user(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get(settings.ACCESS_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_token(token)
        if not is_token_type(payload, "access"):
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
    except Exception:
        return None
    user = await User.get_by_id(db, user_id)
    if not user or not user.is_active:
        return None
    return user


@router.get("/mailboxes", response_model=List[MailboxResponse])
async def list_mailboxes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    result = await db.execute(select(Mailbox).order_by(Mailbox.created_at.asc()))
    return result.scalars().all()


@router.post("/mailboxes", response_model=MailboxResponse)
async def create_mailbox(
    payload: MailboxCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    existing = await db.execute(select(Mailbox).where(Mailbox.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Mailbox already exists")
    mailbox = Mailbox(name=payload.name.strip(), email=payload.email.strip(), provider="yandex", status="new")
    db.add(mailbox)
    await db.commit()
    await db.refresh(mailbox)
    return mailbox


@router.post("/mailboxes/{mailbox_id}/connect", response_model=MailboxAuthUrl)
async def connect_mailbox(
    mailbox_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    if not settings.YANDEX_OAUTH_CLIENT_ID or not settings.YANDEX_OAUTH_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="OAuth для почты не настроен.")
    state = build_state(mailbox_id, str(user.id))
    auth_url = build_auth_url(state, login_hint=mailbox.email)
    return MailboxAuthUrl(auth_url=auth_url)


@router.post("/mailboxes/{mailbox_id}/connect-app-password", response_model=MailboxResponse)
async def connect_mailbox_app_password(
    mailbox_id: str,
    payload: MailboxAppPassword,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    if not payload.app_password or not payload.app_password.strip():
        raise HTTPException(status_code=400, detail="Нужно указать пароль приложения.")
    mailbox.provider = "yandex_app_password"
    mailbox.access_token = payload.app_password.strip()
    mailbox.refresh_token = None
    mailbox.token_expires_at = None
    mailbox.status = "connected"
    await db.commit()
    await db.refresh(mailbox)

    try:
        await sync_mailbox(db, mailbox, limit=2000, since_days=30, mailbox_name="INBOX")
    except Exception as exc:
        mailbox.status = "error"
        await db.commit()
        logger.warning("Initial app-password sync failed for %s: %s", mailbox.email, exc)
    return mailbox


@router.get("/oauth/yandex/callback")
async def yandex_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    state_payload = verify_state(state)
    if not state_payload:
        raise HTTPException(status_code=400, detail="Некорректный OAuth state.")
    mailbox_id = state_payload["mailbox_id"]
    expected_user_id = state_payload["user_id"]
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    current_user = await _get_callback_user(request, db)
    if (
        not current_user
        or str(current_user.id) != str(expected_user_id)
        or not await _user_has_mail_access(None, db, current_user)
    ):
        mailbox.status = "error"
        await db.commit()
        logger.warning("OAuth callback rejected for mailbox %s due to missing/invalid session", mailbox.email)
        return RedirectResponse(url="/mail?connected=0&error=session")
    if error:
        mailbox.status = "error"
        await db.commit()
        logger.warning("OAuth provider error for %s: %s %s", mailbox.email, error, error_description or "")
        return RedirectResponse(url="/mail?connected=0&error=oauth")
    if not code:
        mailbox.status = "error"
        await db.commit()
        logger.warning("OAuth callback missing code for %s", mailbox.email)
        return RedirectResponse(url="/mail?connected=0&error=missing_code")
    try:
        token_data = await exchange_code(code)
    except Exception as exc:
        mailbox.status = "error"
        await db.commit()
        logger.warning("OAuth token exchange failed for %s: %s", mailbox.email, exc)
        return RedirectResponse(url="/mail?connected=0&error=token_exchange")
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in") or 3600)
    mailbox.access_token = access_token
    if refresh_token:
        mailbox.refresh_token = refresh_token
    mailbox.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    mailbox.status = "connected" if access_token else "error"
    await db.commit()
    await db.refresh(mailbox)

    # Initial sync on connect: last 30 days, inbox only, up to 2000 messages.
    if access_token:
        try:
            await sync_mailbox(db, mailbox, limit=2000, since_days=30, mailbox_name="INBOX")
        except Exception as exc:
            mailbox.status = "error"
            await db.commit()
            logger.warning("Initial OAuth sync failed for %s: %s", mailbox.email, exc)

    return RedirectResponse(url="/mail?connected=1")


@router.get("/mailboxes/{mailbox_id}/messages", response_model=MailMessageList)
async def list_messages(
    mailbox_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    folder: str = "inbox",
    refresh: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    folder = (folder or "inbox").strip().lower()
    if folder not in {item["id"] for item in MAIL_FOLDERS}:
        raise HTTPException(status_code=400, detail="Неизвестная папка.")
    limit = max(1, min(int(limit or 50), 100))
    offset = max(0, int(offset or 0))
    try:
        if folder in REAL_MAIL_FOLDERS and refresh and offset == 0:
            await sync_mailbox(db, mailbox, limit=max(limit, 100), mailbox_name=folder, force_since_days=30)
    except Exception as exc:
        mailbox.status = "error"
        await db.commit()
        logger.warning("IMAP sync failed for %s: %s", mailbox.email, exc)
    filters = [MailMessage.mailbox_id == mailbox.id]
    if folder == "important":
        filters.append(MailMessage.flags.like("%\\Flagged%"))
    else:
        filters.append(MailMessage.folder == folder)

    total_result = await db.execute(select(func.count()).select_from(MailMessage).where(*filters))
    total = int(total_result.scalar() or 0)
    result = await db.execute(
        select(MailMessage)
        .where(*filters)
        .order_by(MailMessage.date.desc().nullslast(), MailMessage.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()
    return MailMessageList(
        items=[_serialize_message(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(items) < total,
        folder=folder,
    )


@router.get("/mailboxes/{mailbox_id}/folders", response_model=List[MailFolderResponse])
async def list_folders(
    mailbox_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")

    rows = await db.execute(
        select(
            MailMessage.folder,
            func.count(MailMessage.id),
            func.sum(case((func.coalesce(MailMessage.flags, "").not_like("%\\Seen%"), 1), else_=0)),
        )
        .where(MailMessage.mailbox_id == mailbox.id)
        .group_by(MailMessage.folder)
    )
    stats = {row[0] or "inbox": {"count": int(row[1] or 0), "unread_count": int(row[2] or 0)} for row in rows.all()}
    important_result = await db.execute(
        select(func.count(MailMessage.id))
        .where(MailMessage.mailbox_id == mailbox.id, MailMessage.flags.like("%\\Flagged%"))
    )
    stats["important"] = {"count": int(important_result.scalar() or 0), "unread_count": 0}
    return [
        MailFolderResponse(
            id=item["id"],
            label=item["label"],
            icon=item["icon"],
            count=stats.get(item["id"], {}).get("count", 0),
            unread_count=stats.get(item["id"], {}).get("unread_count", 0),
        )
        for item in MAIL_FOLDERS
    ]


@router.get("/messages/{message_id}")
async def get_message_body(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    message = await db.get(MailMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Письмо не найдено.")
    mailbox = await db.get(Mailbox, message.mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    mailbox = await ensure_valid_token(db, mailbox)
    if not mailbox.access_token:
        raise HTTPException(status_code=400, detail="Почтовый ящик не авторизован.")

    auth_mode = "oauth"
    password = None
    if mailbox.provider == "yandex_app_password":
        auth_mode = "password"
        password = mailbox.access_token or ""

    try:
        data = await asyncio.to_thread(
            fetch_message_body,
            mailbox.email,
            mailbox.access_token,
            _message_imap_uid(message),
            message.folder or "inbox",
            auth_mode,
            password,
            str(message.id),
        )
    except Exception as exc:
        logger.warning("IMAP body fetch failed for %s: %s", mailbox.email, exc)
        raise HTTPException(status_code=500, detail="Не удалось загрузить тело письма.")

    if data.get("cc_addr") is not None and data.get("cc_addr") != message.cc_addr:
        message.cc_addr = data.get("cc_addr") or None
        await db.commit()

    if not (data.get("body") or "").strip() and message.snippet:
        cleaned = normalize_snippet_text(message.snippet)
        if cleaned:
            if re.search(r"</?(html|body|head|div|p|table|br|span|meta|style)\b", cleaned, re.I) or re.search(r"<!doctype", cleaned, re.I):
                return {
                    "body": cleaned,
                    "body_html": cleaned,
                    "content_type": "text/html",
                    "attachments": data.get("attachments") or [],
                    "cc_addr": data.get("cc_addr") or message.cc_addr or "",
                }
            return {
                "body": cleaned,
                "body_text": cleaned,
                "content_type": "text/plain",
                "attachments": data.get("attachments") or [],
                "cc_addr": data.get("cc_addr") or message.cc_addr or "",
            }

    return data


@router.get("/messages/{message_id}/attachments/{attachment_id}")
async def download_message_attachment(
    message_id: str,
    attachment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    message = await db.get(MailMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Письмо не найдено.")
    mailbox = await db.get(Mailbox, message.mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    mailbox = await ensure_valid_token(db, mailbox)
    if not mailbox.access_token:
        raise HTTPException(status_code=400, detail="Почтовый ящик не авторизован.")

    auth_mode = "oauth"
    password = None
    if mailbox.provider == "yandex_app_password":
        auth_mode = "password"
        password = mailbox.access_token or ""

    try:
        data = await asyncio.to_thread(
            fetch_message_attachment,
            mailbox.email,
            mailbox.access_token,
            _message_imap_uid(message),
            attachment_id,
            message.folder or "inbox",
            auth_mode,
            password,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc) or "Вложение заблокировано политикой безопасности.")
    except ValueError as exc:
        code = str(exc)
        if code == "invalid_attachment_id":
            raise HTTPException(status_code=400, detail="Некорректный идентификатор вложения.")
        if code == "attachment_not_found":
            raise HTTPException(status_code=404, detail="Вложение не найдено.")
        if code == "attachment_too_large":
            raise HTTPException(status_code=413, detail="Вложение превышает допустимый размер.")
        raise HTTPException(status_code=400, detail="Не удалось загрузить вложение.")
    except Exception as exc:
        logger.warning("IMAP attachment fetch failed for %s: %s", mailbox.email, exc)
        raise HTTPException(status_code=500, detail="Не удалось загрузить вложение.")

    filename = data.get("filename") or "attachment"
    return Response(
        content=data.get("content") or b"",
        media_type=_safe_attachment_media_type(data.get("content_type")),
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.post("/messages/{message_id}/move", response_model=MailMessageResponse)
async def move_mail_message(
    message_id: str,
    payload: MailMessageMoveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    target = (payload.target or "").strip().lower()
    if target not in {"archive", "spam", "trash", "inbox"}:
        raise HTTPException(status_code=400, detail="Неверная целевая папка.")
    message = await db.get(MailMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Письмо не найдено.")
    mailbox = await db.get(Mailbox, message.mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    mailbox = await ensure_valid_token(db, mailbox)
    if not mailbox.access_token:
        raise HTTPException(status_code=400, detail="Почтовый ящик не авторизован.")

    auth_mode, password = _mail_auth(mailbox)
    source_uid = _message_imap_uid(message)
    try:
        target_uid = await asyncio.to_thread(
            move_message_to_folder,
            mailbox.email,
            mailbox.access_token,
            source_uid,
            message.folder or "inbox",
            target,
            auth_mode,
            password,
        )
    except Exception as exc:
        logger.warning("IMAP move failed for %s message %s to %s: %s", mailbox.email, message.id, target, exc)
        raise HTTPException(status_code=500, detail="Не удалось переместить письмо.")

    message.folder = target
    message.uid = _storage_uid(target, target_uid or source_uid)
    await db.commit()
    await db.refresh(message)
    return _serialize_message(message)


@router.post("/mailboxes/{mailbox_id}/send", response_model=MailSendResponse)
async def send_mail(
    mailbox_id: str,
    payload: MailSendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    mailbox = await ensure_valid_token(db, mailbox)
    if not mailbox.access_token:
        raise HTTPException(status_code=400, detail="Почтовый ящик не авторизован.")
    try:
        # SMTP is blocking: run in thread with timeout handled by SMTP lib.
        import asyncio
        await asyncio.to_thread(
            send_message,
            mailbox.email,
            mailbox.access_token,
            payload.to,
            payload.subject,
            payload.body,
            payload.cc,
            payload.bcc,
            "password" if mailbox.provider == "yandex_app_password" else "oauth",
            mailbox.access_token if mailbox.provider == "yandex_app_password" else "",
        )
    except MailSendAuthenticationError as exc:
        logger.warning("SMTP auth failed for %s: %s", mailbox.email, exc)
        raise HTTPException(
            status_code=400,
            detail="SMTP авторизация не прошла. Проверьте пароль приложения или переподключите почтовый ящик.",
        )
    except MailSendTransportError as exc:
        logger.warning("SMTP transport unavailable for %s: %s", mailbox.email, exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "SMTP недоступен с сервера. Вероятно, на VPS заблокированы исходящие порты "
                "465/587. Нужно разблокировать SMTP у провайдера или настроить внешний SMTP relay."
            ),
        )
    except Exception as exc:
        logger.warning("SMTP send failed for %s: %s", mailbox.email, exc)
        raise HTTPException(status_code=500, detail="Не удалось отправить письмо.")
    # Эмитим после успешной отправки — нужно для BI (трекинг исходящих)
    # и для FTS-индекса (если решим индексировать исходящие).
    await emit_event_safe(
        db,
        event_type="mail_message.after_send",
        entity_type="mail_message",
        entity_id=str(mailbox.id),
        payload={
            "mailbox_id": str(mailbox.id),
            "from": mailbox.email,
            "to": payload.to,
            "cc": payload.cc,
            "bcc": payload.bcc,
            "subject": payload.subject,
            "sender_user_id": str(user.id),
        },
        payload_version=1,
    )
    return MailSendResponse(message="ok")


@router.delete("/mailboxes/{mailbox_id}")
async def delete_mailbox(
    mailbox_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    await db.execute(delete(MailMessage).where(MailMessage.mailbox_id == mailbox.id))
    await db.delete(mailbox)
    await db.commit()
    return {"ok": True}


@router.get("/mailboxes/{mailbox_id}/export")
async def export_mailbox(
    mailbox_id: str,
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_mail_access(request, db, user)
    mailbox = await db.get(Mailbox, mailbox_id)
    if not mailbox:
        raise HTTPException(status_code=404, detail="Почтовый ящик не найден.")
    days = max(1, min(int(days or 30), 365))
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(MailMessage)
        .where(MailMessage.mailbox_id == mailbox.id)
        .where(MailMessage.date.is_(None) | (MailMessage.date >= since))
        .order_by(MailMessage.date.desc().nullslast())
    )
    items = result.scalars().all()
    # Build CSV
    import csv
    import io

    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(["date", "from", "to", "cc", "subject", "snippet", "message_id", "uid"])
    for item in items:
        writer.writerow([
            item.date.isoformat() if item.date else "",
            item.from_addr or "",
            item.to_addr or "",
            item.cc_addr or "",
            item.subject or "",
            (item.snippet or "").replace("\n", " ").strip(),
            item.message_id or "",
            item.uid or "",
        ])
    filename = f"mailbox_{mailbox.email}_{days}d.csv".replace("@", "_")
    return Response(
        content=out.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
