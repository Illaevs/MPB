"""
Mailbox model - OAuth connected mailboxes.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from app.database.base import Base


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    email = Column(String(255), nullable=False)
    provider = Column(String(32), default="yandex")
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), default="new")
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_uid = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
