"""
Notification delivery queue for external channels.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("notification_id", "channel", name="uq_notification_delivery_channel"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(32), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="pending", index=True)
    destination = Column(String(255))
    payload = Column(JSON, default=dict)
    attempt_count = Column(Integer, default=0)
    next_attempt_at = Column(DateTime(timezone=True), index=True)
    sent_at = Column(DateTime(timezone=True))
    provider_message_id = Column(String(128))
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
