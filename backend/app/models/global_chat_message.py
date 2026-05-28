"""
Global chat message model.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class GlobalChatMessage(Base):
    __tablename__ = "global_chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("chat_conversations.id"), nullable=True)
    reply_to_message_id = Column(String(36), ForeignKey("global_chat_messages.id"), nullable=True)
    forwarded_from_message_id = Column(String(36), ForeignKey("global_chat_messages.id"), nullable=True)

    body = Column(Text, nullable=True)
    attachments = Column(JSON, default=list)
    mentions = Column(JSON, default=list)

    is_deleted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    pinned_at = Column(DateTime(timezone=True), nullable=True)
    pinned_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    conversation = relationship("ChatConversation", back_populates="messages")
    pinned_by = relationship("User", foreign_keys=[pinned_by_user_id])
    reply_to_message = relationship(
        "GlobalChatMessage",
        remote_side=[id],
        foreign_keys=[reply_to_message_id],
        post_update=True,
    )
    forwarded_from_message = relationship(
        "GlobalChatMessage",
        remote_side=[id],
        foreign_keys=[forwarded_from_message_id],
        post_update=True,
    )
