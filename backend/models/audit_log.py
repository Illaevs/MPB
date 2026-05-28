"""
AuditLog model for system-wide auditing.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(64), index=True)
    action = Column(String(100), nullable=False)
    user_id = Column(String(36))
    source_event_id = Column(String(64), index=True)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def create(cls, db, **kwargs):
        entry = cls(**kwargs)
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry
