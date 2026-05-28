"""
Telegram notification connection endpoints.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import TelegramConnection, User
from app.schemas.notification_rules import TelegramConnectionStatusResponse, TelegramLinkResponse
from app.services.telegram_bot import build_telegram_deep_link, telegram_bot_configured, utcnow_naive
from app.services.telegram_updates import (
    get_or_create_notification_preference,
    handle_telegram_update,
)

router = APIRouter()


def _mask_chat_id(chat_id: Optional[str]) -> Optional[str]:
    if not chat_id:
        return None
    value = str(chat_id)
    if len(value) <= 4:
        return value
    return f"{'*' * max(0, len(value) - 4)}{value[-4:]}"


async def _get_connection_by_user(db: AsyncSession, user_id: str) -> Optional[TelegramConnection]:
    result = await db.execute(
        select(TelegramConnection).where(TelegramConnection.user_id == str(user_id))
    )
    return result.scalar_one_or_none()


@router.get("/me", response_model=TelegramConnectionStatusResponse)
async def get_my_telegram_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    pref = await get_or_create_notification_preference(db, str(user.id))
    connection = await _get_connection_by_user(db, str(user.id))
    return TelegramConnectionStatusResponse(
        bot_configured=telegram_bot_configured(),
        bot_username=settings.TELEGRAM_BOT_USERNAME or None,
        is_connected=bool(connection and connection.chat_id and connection.is_verified),
        is_enabled=bool(connection.is_enabled) if connection else False,
        is_verified=bool(connection.is_verified) if connection else False,
        telegram_username=(f"@{connection.username}" if connection and connection.username else None),
        chat_id_masked=_mask_chat_id(connection.chat_id if connection else None),
        linked_at=connection.linked_at if connection else None,
        deliver_telegram=bool(pref.deliver_telegram),
    )


@router.post("/link", response_model=TelegramLinkResponse)
async def create_telegram_link(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if not telegram_bot_configured():
        return TelegramLinkResponse(
            bot_configured=False,
            bot_username=settings.TELEGRAM_BOT_USERNAME or None,
            link_url=None,
            expires_at=None,
        )

    now = utcnow_naive()
    expires_at = now + timedelta(minutes=max(1, int(settings.TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES or 30)))
    token = secrets.token_urlsafe(32)

    connection = await _get_connection_by_user(db, str(user.id))
    if not connection:
        connection = TelegramConnection(
            user_id=str(user.id),
            is_enabled=True,
            is_verified=False,
        )
        db.add(connection)

    connection.is_enabled = True
    connection.link_token = token
    connection.link_token_expires_at = expires_at
    await db.commit()

    return TelegramLinkResponse(
        bot_configured=True,
        bot_username=settings.TELEGRAM_BOT_USERNAME or None,
        link_url=build_telegram_deep_link(token),
        expires_at=expires_at,
    )


@router.delete("/me")
async def unlink_my_telegram(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    connection = await _get_connection_by_user(db, str(user.id))
    if connection:
        connection.telegram_user_id = None
        connection.chat_id = None
        connection.username = None
        connection.first_name = None
        connection.last_name = None
        connection.is_enabled = False
        connection.is_verified = False
        connection.link_token = None
        connection.link_token_expires_at = None
        connection.linked_at = None
        connection.last_seen_at = None

    pref = await get_or_create_notification_preference(db, str(user.id))
    pref.deliver_telegram = False
    await db.commit()
    return {"message": "telegram_unlinked"}


@router.post("/webhook/{webhook_secret}")
async def telegram_webhook(
    webhook_secret: str,
    payload: Optional[dict[str, Any]] = Body(None),
    db: AsyncSession = Depends(get_db),
):
    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET or ""
    if not expected_secret or webhook_secret != expected_secret:
        raise HTTPException(status_code=404, detail="Not found")
    return await handle_telegram_update(db, payload)
