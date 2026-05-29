"""Реакции эмодзи на сообщения чата (Phase B.3 plan messenger-implicit-dm).

Дизайн:
  - Один (message_id, user_id, emoji) = одна строка. Уникальный
    constraint защищает от двойного клика / race condition.
  - emoji — VARCHAR(32). По умолчанию используем юникодные эмодзи
    (👍 ❤️ 😂 ...), но при желании можно расширить кастомными
    sticker-id'ами.
  - Soft delete не используется: убрать реакцию = удалить строку
    (history/audit при необходимости — отдельный механизм).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ChatMessageReaction(Base):
    __tablename__ = "chat_message_reactions"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "user_id", "emoji",
            name="uq_chat_message_reactions_unique",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36),
        ForeignKey("global_chat_messages.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    emoji = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
