"""
Mail sync helpers (token refresh + IMAP fetch + DB upsert).
"""
import asyncio
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Mailbox, MailMessage
from app.services.mail_imap import fetch_recent_messages
from app.services.yandex_oauth import refresh_token as refresh_oauth


def _storage_uid(folder_key: str, uid: str) -> str:
    uid = str(uid or "")
    if folder_key == "inbox" or uid.startswith(f"{folder_key}:"):
        return uid
    return f"{folder_key}:{uid}"


async def ensure_valid_token(db: AsyncSession, mailbox: Mailbox) -> Mailbox:
    if not mailbox.refresh_token:
        return mailbox
    if mailbox.access_token and mailbox.token_expires_at:
        buffer_time = datetime.utcnow() + timedelta(seconds=60)
        if mailbox.token_expires_at > buffer_time:
            return mailbox
    try:
        data = await refresh_oauth(mailbox.refresh_token)
        mailbox.access_token = data.get("access_token") or mailbox.access_token
        mailbox.refresh_token = data.get("refresh_token") or mailbox.refresh_token
        expires_in = int(data.get("expires_in") or 3600)
        mailbox.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        mailbox.status = "connected"
        await db.commit()
        await db.refresh(mailbox)
    except Exception as exc:
        mailbox.status = "error"
        mailbox.access_token = None
        await db.commit()
        print(f"[mail] token refresh error for {mailbox.email}: {exc}")
    return mailbox


async def sync_mailbox(
    db: AsyncSession,
    mailbox: Mailbox,
    limit: int = 50,
    since_days: int | None = None,
    mailbox_name: str = "INBOX",
    force_since_days: int | None = None,
) -> List[MailMessage]:
    mailbox = await ensure_valid_token(db, mailbox)
    if not mailbox.access_token:
        return []

    normalized_folder = (mailbox_name or "INBOX").strip().lower()
    folder_key = {
        "inbox": "inbox",
        "sent": "sent",
        "archive": "archive",
        "spam": "spam",
        "trash": "trash",
        "drafts": "drafts",
    }.get(normalized_folder, normalized_folder)

    since_dt = None
    last_uid = mailbox.last_uid if folder_key == "inbox" else None
    if force_since_days is not None:
        since_dt = datetime.utcnow() - timedelta(days=force_since_days)
        last_uid = None
    elif since_days:
        since_dt = datetime.utcnow() - timedelta(days=since_days)

    auth_mode = "oauth"
    password = None
    if mailbox.provider == "yandex_app_password":
        auth_mode = "password"
        password = mailbox.access_token or ""

    messages = await asyncio.to_thread(
        fetch_recent_messages,
        mailbox.email,
        mailbox.access_token,
        last_uid,
        limit,
        since_dt,
        mailbox_name,
        auth_mode,
        password,
    )

    if not messages:
        mailbox.last_sync_at = datetime.utcnow()
        await db.commit()
        return []

    storage_uids = [
        _storage_uid(folder_key, m.get("uid"))
        for m in messages
        if m.get("uid")
    ]
    result = await db.execute(
        select(MailMessage).where(
            MailMessage.mailbox_id == mailbox.id,
            MailMessage.folder == folder_key,
            MailMessage.uid.in_(storage_uids),
        )
    )
    existing_map = {row[0].uid: row[0] for row in result.fetchall()}

    created = []
    for item in messages:
        uid = item.get("uid")
        if not uid:
            continue
        cache_uid = _storage_uid(folder_key, uid)
        existing_msg = existing_map.get(cache_uid)
        if existing_msg:
            # Refresh cached headers/snippet for already imported messages
            existing_msg.message_id = item.get("message_id")
            existing_msg.subject = item.get("subject")
            existing_msg.from_addr = item.get("from_addr")
            existing_msg.to_addr = item.get("to_addr")
            existing_msg.cc_addr = item.get("cc_addr")
            existing_msg.date = item.get("date")
            existing_msg.snippet = item.get("snippet")
            existing_msg.flags = item.get("flags")
            existing_msg.has_attachments = bool(item.get("has_attachments"))
            continue
        msg = MailMessage(
            mailbox_id=mailbox.id,
            uid=cache_uid,
            folder=folder_key,
            message_id=item.get("message_id"),
            subject=item.get("subject"),
            from_addr=item.get("from_addr"),
            to_addr=item.get("to_addr"),
            cc_addr=item.get("cc_addr"),
            date=item.get("date"),
            snippet=item.get("snippet"),
            flags=item.get("flags"),
            has_attachments=bool(item.get("has_attachments")),
        )
        db.add(msg)
        created.append(msg)

    if folder_key == "inbox":
        mailbox.last_uid = messages[-1].get("uid") or mailbox.last_uid
    mailbox.last_sync_at = datetime.utcnow()
    if created:
        await db.commit()
        for msg in created:
            await db.refresh(msg)
    else:
        await db.commit()
    return created
