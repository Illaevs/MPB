"""
Notification subscription model.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_notification_subscription"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    is_muted = Column(Boolean, default=False)
    mute_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
