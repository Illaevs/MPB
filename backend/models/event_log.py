"""
EventLog model – simple audit trail.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from app.database.base import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def create(cls, db, **kwargs):
        work = cls(**kwargs)
        db.add(work)
        await db.commit()
        await db.refresh(work)
        return work

