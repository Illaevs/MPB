"""
Telegram bot connection for a user.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class TelegramConnection(Base):
    __tablename__ = "telegram_connections"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_telegram_connection_user"),
        UniqueConstraint("chat_id", name="uq_telegram_connection_chat"),
        UniqueConstraint("link_token", name="uq_telegram_connection_link_token"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    telegram_user_id = Column(String(64), index=True)
    chat_id = Column(String(64), index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_enabled = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    link_token = Column(String(128), index=True)
    link_token_expires_at = Column(DateTime(timezone=True))
    linked_at = Column(DateTime(timezone=True))
    last_seen_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
