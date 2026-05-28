"""
MailMessage model - cached headers/snippets from IMAP.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class MailMessage(Base):
    __tablename__ = "mail_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mailbox_id = Column(String(36), ForeignKey("mailboxes.id"), nullable=False)
    uid = Column(String(64), nullable=False)
    folder = Column(String(64), nullable=False, default="inbox")
    message_id = Column(String(255), nullable=True)
    subject = Column(String(512), nullable=True)
    from_addr = Column(String(512), nullable=True)
    to_addr = Column(String(1024), nullable=True)
    cc_addr = Column(String(1024), nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    snippet = Column(Text, nullable=True)
    flags = Column(String(255), nullable=True)
    has_attachments = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("mailbox_id", "uid", name="uq_mail_messages_mailbox_uid"),
    )
