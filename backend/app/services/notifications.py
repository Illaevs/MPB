"""
Service helper for creating notifications.
"""
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification
from app.services.notification_delivery import enqueue_telegram_delivery_for_notification


async def create_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    message: Optional[str] = None,
    type: str = "info",
    priority: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action_url: Optional[str] = None,
    rule_id: Optional[str] = None,
    source_event_id: Optional[str] = None,
    deliver_at: Optional[datetime] = None,
) -> Notification:
    notification = await Notification.create(
        db,
        user_id=str(user_id),
        type=type,
        priority=priority or type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
        rule_id=rule_id,
        source_event_id=source_event_id,
        deliver_at=deliver_at,
        is_read=False,
    )
    await enqueue_telegram_delivery_for_notification(db, notification)
    return notification
