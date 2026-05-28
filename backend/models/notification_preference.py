"""
Notification preferences per user.
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.database.base import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id = Column(String(36), primary_key=True)
    timezone = Column(String(64), default="Europe/Moscow")
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="08:00")
    digest_enabled = Column(Boolean, default=True)
    digest_time = Column(String(5), default="09:00")
    deliver_in_app = Column(Boolean, default=True)
    deliver_telegram = Column(Boolean, default=False)
    digest_last_sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
