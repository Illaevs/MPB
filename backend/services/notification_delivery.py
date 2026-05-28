"""
Notification delivery helpers for external channels.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationDelivery, NotificationPreference, NotificationRule, TelegramConnection
from app.services.telegram_bot import build_telegram_message, send_telegram_message, telegram_bot_configured, utcnow_naive


MAX_TELEGRAM_ATTEMPTS = 5
HEALTH_REPORT_CALLBACK = "data_health_report_pdf"


def _data_health_reply_markup(action_url: Optional[str]) -> Optional[dict]:
    if action_url != "/data-health":
        return None
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


async def enqueue_telegram_delivery_for_notification(
    db: AsyncSession,
    notification: Notification,
) -> Optional[NotificationDelivery]:
    if not notification or not notification.rule_id or not telegram_bot_configured():
        return None

    rule = await NotificationRule.get_by_id(db, str(notification.rule_id))
    if not rule or not rule.deliver_telegram:
        return None

    pref_result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == str(notification.user_id))
    )
    pref = pref_result.scalar_one_or_none()
    if not pref or not pref.deliver_telegram:
        return None

    connection_result = await db.execute(
        select(TelegramConnection).where(
            TelegramConnection.user_id == str(notification.user_id),
            TelegramConnection.is_enabled.is_(True),
            TelegramConnection.is_verified.is_(True),
            TelegramConnection.chat_id.is_not(None),
        )
    )
    connection = connection_result.scalar_one_or_none()
    if not connection or not connection.chat_id:
        return None

    existing_result = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.notification_id == str(notification.id),
            NotificationDelivery.channel == "telegram",
        )
    )
    if existing_result.scalar_one_or_none():
        return None

    payload = {
        "title": notification.title,
        "message": notification.message,
        "action_url": notification.action_url,
    }
    next_attempt_at = notification.deliver_at or utcnow_naive()
    delivery = NotificationDelivery(
        notification_id=str(notification.id),
        user_id=str(notification.user_id),
        channel="telegram",
        status="pending",
        destination=str(connection.chat_id),
        payload=payload,
        next_attempt_at=next_attempt_at,
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)
    return delivery


def _next_retry_time(attempt_count: int):
    delay_minutes = min(60, 2 ** max(0, attempt_count - 1))
    return utcnow_naive() + timedelta(minutes=delay_minutes)


async def process_telegram_deliveries(db: AsyncSession, *, limit: int = 50) -> None:
    if not telegram_bot_configured():
        return

    now = utcnow_naive()
    result = await db.execute(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.channel == "telegram",
            NotificationDelivery.status.in_(("pending", "retry")),
            (
                NotificationDelivery.next_attempt_at.is_(None)
            ) | (
                NotificationDelivery.next_attempt_at <= now
            ),
        )
        .order_by(NotificationDelivery.created_at.asc())
        .limit(limit)
    )
    deliveries = result.scalars().all()

    for delivery in deliveries:
        try:
            connection_result = await db.execute(
                select(TelegramConnection).where(
                    TelegramConnection.user_id == str(delivery.user_id),
                    TelegramConnection.is_enabled.is_(True),
                    TelegramConnection.is_verified.is_(True),
                    TelegramConnection.chat_id.is_not(None),
                )
            )
            connection = connection_result.scalar_one_or_none()
            if not connection or not connection.chat_id:
                delivery.status = "skipped"
                delivery.last_error = "Telegram connection is missing or disabled"
                delivery.next_attempt_at = None
                await db.commit()
                continue

            payload = delivery.payload or {}
            message = build_telegram_message(
                payload.get("title") or "Уведомление",
                payload.get("message"),
                payload.get("action_url"),
            )
            response = await send_telegram_message(
                str(connection.chat_id),
                message,
                reply_markup=_data_health_reply_markup(payload.get("action_url")),
            )

            delivery.destination = str(connection.chat_id)
            delivery.provider_message_id = str(response.get("message_id") or "")
            delivery.status = "sent"
            delivery.sent_at = utcnow_naive()
            delivery.last_error = None
            delivery.attempt_count = int(delivery.attempt_count or 0) + 1
            delivery.next_attempt_at = None
            connection.last_seen_at = utcnow_naive()
            await db.commit()
        except Exception as error:
            delivery.attempt_count = int(delivery.attempt_count or 0) + 1
            delivery.last_error = str(error)[:2000]
            if delivery.attempt_count >= MAX_TELEGRAM_ATTEMPTS:
                delivery.status = "failed"
                delivery.next_attempt_at = None
            else:
                delivery.status = "retry"
                delivery.next_attempt_at = _next_retry_time(delivery.attempt_count)
            await db.commit()
