"""
LeadActivity model — feed of events around a lead (comments, file uploads,
status changes, task links, etc.) for the Bitrix-style timeline.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False, index=True)

    # 'comment' | 'status_change' | 'field_change' | 'file' | 'task_link' | 'convert' | 'created' | 'system'
    activity_type = Column(String(32), nullable=False, index=True)

    # Free-text content (comment body, change description, file caption)
    content = Column(Text)

    # Structured payload: { from, to, file_path, file_name, file_size, task_id, ... }
    payload = Column(JSON, default=dict)

    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    @classmethod
    async def create(cls, db, **kwargs):
        kwargs.setdefault("created_at", datetime.now())
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def list_for_lead(cls, db, lead_id: str, *, limit: int = 200, offset: int = 0):
        from sqlalchemy import select
        query = (
            select(cls)
            .where(cls.lead_id == str(lead_id))
            .order_by(cls.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def delete(cls, db, activity_id: str) -> bool:
        from sqlalchemy import delete
        result = await db.execute(delete(cls).where(cls.id == str(activity_id)))
        await db.commit()
        return result.rowcount > 0
