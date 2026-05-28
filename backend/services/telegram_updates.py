"""
Telegram bot update processing.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationPreference, TelegramConnection
from app.services.data_health import refresh_all_health_issues
from app.services.data_health_report import build_data_health_report_pdf
from app.services.telegram_bot import (
    answer_telegram_callback_query,
    send_telegram_document,
    send_telegram_message,
    telegram_bot_configured,
    utcnow_naive,
)
from app.services.telegram_commands import (
    handle_telegram_command,
    health_report_allowed_deal_ids,
    help_text,
)


logger = logging.getLogger(__name__)
HEALTH_REPORT_CALLBACK = "data_health_report_pdf"


def health_report_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "PDF health-check",
                    "callback_data": HEALTH_REPORT_CALLBACK,
                }
            ]
        ]
    }


async def get_or_create_notification_preference(
    db: AsyncSession,
    user_id: str,
) -> NotificationPreference:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == str(user_id))
    )
    pref = result.scalar_one_or_none()
    if pref:
        return pref
    pref = NotificationPreference(user_id=str(user_id))
    db.add(pref)
    await db.flush()
    return pref


async def get_connection_by_chat_id(
    db: AsyncSession,
    chat_id: str,
) -> Optional[TelegramConnection]:
    result = await db.execute(
        select(TelegramConnection).where(TelegramConnection.chat_id == str(chat_id))
    )
    return result.scalar_one_or_none()


async def send_safe_message(chat_id: Optional[str], text: str, *, reply_markup: Optional[dict] = None) -> None:
    if not chat_id or not telegram_bot_configured():
        return
    try:
        await send_telegram_message(str(chat_id), text, reply_markup=reply_markup)
    except Exception as error:
        logger.warning("Telegram safe message failed: %s", error)


async def _send_health_report(db: AsyncSession, chat_id: Optional[str]) -> None:
    if not chat_id:
        return

    connection = await get_connection_by_chat_id(db, str(chat_id))
    if not connection or not connection.is_enabled or not connection.is_verified or not connection.user_id:
        await send_safe_message(
            str(chat_id),
            "Сначала привяжите Telegram к пользователю в системе, затем повторите команду /health.",
        )
        return

    try:
        allowed_deal_ids = await health_report_allowed_deal_ids(db, str(chat_id))
    except PermissionError:
        await send_safe_message(str(chat_id), "Нет доступа к PDF-отчету контроля данных.")
        return

    await send_safe_message(str(chat_id), "Формирую PDF-отчет контроля данных...")
    await refresh_all_health_issues(db)
    pdf_bytes = await build_data_health_report_pdf(
        db,
        status="active",
        grouped=True,
        limit=1000,
        allowed_deal_ids=allowed_deal_ids,
    )
    today_key = utcnow_naive().strftime("%Y-%m-%d")
    await send_telegram_document(
        str(chat_id),
        pdf_bytes,
        f"data-health-{today_key}.pdf",
        caption="PDF-отчет контроля данных",
    )
    connection.last_seen_at = utcnow_naive()
    await db.commit()


async def _handle_callback_query(
    db: AsyncSession,
    callback: dict[str, Any],
) -> dict[str, bool]:
    callback_id = callback.get("id")
    callback_data = callback.get("data")
    callback_message = callback.get("message") or {}
    callback_chat = callback_message.get("chat") or {}
    chat_id = callback_chat.get("id")

    if callback_data != HEALTH_REPORT_CALLBACK:
        if callback_id:
            await answer_telegram_callback_query(callback_id)
        return {"ok": True}

    try:
        if callback_id:
            await answer_telegram_callback_query(callback_id, text="Формирую PDF...")
        await _send_health_report(db, str(chat_id) if chat_id is not None else None)
    except Exception as error:
        logger.warning("Telegram health report callback failed: %s", error)
        if callback_id:
            await answer_telegram_callback_query(callback_id, text="Не удалось сформировать отчет", show_alert=True)
        if chat_id:
            await send_safe_message(str(chat_id), "Не удалось сформировать PDF-отчет. Попробуйте позже.")
    return {"ok": True}


async def _handle_health_command(db: AsyncSession, chat_id: Optional[Any]) -> dict[str, bool]:
    try:
        await _send_health_report(db, str(chat_id) if chat_id is not None else None)
    except Exception as error:
        logger.warning("Telegram health report command failed: %s", error)
        if chat_id:
            await send_safe_message(str(chat_id), "Не удалось сформировать PDF-отчет. Попробуйте позже.")
    return {"ok": True}

async def handle_telegram_update(
    db: AsyncSession,
    payload: Optional[dict[str, Any]],
) -> dict[str, bool]:
    payload = payload or {}

    callback = payload.get("callback_query") or {}
    if callback:
        return await _handle_callback_query(db, callback)

    message = payload.get("message") or payload.get("edited_message") or {}
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    text = (message.get("text") or "").strip()
    chat_id = chat.get("id")

    if await handle_telegram_command(db, chat_id, text, send_health_report=_send_health_report):
        return {"ok": True}

    if not text.startswith("/start"):
        if chat_id:
            await send_safe_message(
                str(chat_id),
                help_text(),
                reply_markup=health_report_keyboard(),
            )
        return {"ok": True}

    token = ""
    parts = text.split(maxsplit=1)
    if len(parts) > 1:
        token = parts[1].strip()
    if not token:
        if chat_id:
            await send_safe_message(
                str(chat_id),
                "Токен привязки не найден. Сгенерируйте новую ссылку в системе.",
            )
        return {"ok": True}

    now = utcnow_naive()
    result = await db.execute(
        select(TelegramConnection).where(
            TelegramConnection.link_token == token,
            TelegramConnection.link_token_expires_at.is_not(None),
            TelegramConnection.link_token_expires_at >= now,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        if chat_id:
            await send_safe_message(
                str(chat_id),
                "Ссылка привязки недействительна или истекла. Сгенерируйте новую в системе.",
            )
        return {"ok": True}

    if chat_id is not None:
        existing_chat_connection = await get_connection_by_chat_id(db, str(chat_id))
        if existing_chat_connection and str(existing_chat_connection.user_id) != str(connection.user_id):
            existing_chat_connection.telegram_user_id = None
            existing_chat_connection.chat_id = None
            existing_chat_connection.username = None
            existing_chat_connection.first_name = None
            existing_chat_connection.last_name = None
            existing_chat_connection.is_enabled = False
            existing_chat_connection.is_verified = False
            existing_chat_connection.link_token = None
            existing_chat_connection.link_token_expires_at = None
            existing_chat_connection.linked_at = None
            existing_chat_connection.last_seen_at = None
            previous_pref = await get_or_create_notification_preference(
                db, str(existing_chat_connection.user_id)
            )
            previous_pref.deliver_telegram = False

    connection.telegram_user_id = str(from_user.get("id") or "") or None
    connection.chat_id = str(chat_id) if chat_id is not None else None
    connection.username = from_user.get("username")
    connection.first_name = from_user.get("first_name")
    connection.last_name = from_user.get("last_name")
    connection.is_enabled = True
    connection.is_verified = True
    connection.link_token = None
    connection.link_token_expires_at = None
    connection.linked_at = now
    connection.last_seen_at = now

    pref = await get_or_create_notification_preference(db, str(connection.user_id))
    pref.deliver_telegram = True
    await db.commit()

    if chat_id:
        await send_safe_message(
            str(chat_id),
            "Telegram-уведомления подключены. Дальше уведомления будут приходить сюда. Команда /health выгружает PDF-отчет контроля данных.",
            reply_markup=health_report_keyboard(),
        )

    return {"ok": True}
