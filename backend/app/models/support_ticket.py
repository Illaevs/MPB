"""
Support tickets (Тех. поддержка) — обращения пользователей + чат.

Видимость: у тикета есть публичная переписка (юзер ↔ поддержка) и
внутренние заметки поддержки (is_internal=True) — юзер их не видит.
"""
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    number = Column(Integer, nullable=True, index=True, unique=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text)
    # bug | improvement | access | question | other
    category = Column(String(32), nullable=False, default="other")
    # new | in_progress | waiting_user | resolved | closed | rejected
    status = Column(String(32), nullable=False, default="new")

    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    assignee_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    linked_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)

    attachments = Column(JSON, default=list)  # файлы, приложенные при создании

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    assignee = relationship("User", foreign_keys=[assignee_id])


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("support_tickets.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    body = Column(Text, nullable=True)
    attachments = Column(JSON, default=list)
    # Внутренняя заметка поддержки — не отдаётся заявителю.
    is_internal = Column(Boolean, default=False, nullable=False)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
