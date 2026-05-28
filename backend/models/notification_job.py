"""
Notification job metadata for background processing.
"""
from sqlalchemy import Column, String, DateTime

from app.database.base import Base


class NotificationJob(Base):
    __tablename__ = "notification_jobs"

    name = Column(String(64), primary_key=True)
    last_run_at = Column(DateTime(timezone=True))
