"""
Notification model for in-app user alerts.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), default="info")
    priority = Column(String(16), default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text)
    entity_type = Column(String(64))
    entity_id = Column(String(64))
    action_url = Column(String(255))
    rule_id = Column(String(36))
    source_event_id = Column(String(64))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    deliver_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs.setdefault("created_at", now)
        notification = cls(**kwargs)
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @classmethod
    async def list_by_user(
        cls,
        db,
        user_id: str,
        unread: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
        type_filter: Optional[str] = None,
        priority: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ):
        from sqlalchemy import select, or_
        query = select(cls).where(
            cls.user_id == str(user_id),
            ((cls.deliver_at.is_(None)) | (cls.deliver_at <= datetime.utcnow())),
        )
        if unread is True:
            query = query.where(cls.is_read.is_(False))
        if type_filter:
            query = query.where(cls.type == type_filter)
        if priority:
            query = query.where(cls.priority == priority)
        if date_from:
            query = query.where(cls.created_at >= date_from)
        if date_to:
            query = query.where(cls.created_at <= date_to)
        if entity_type:
            query = query.where(cls.entity_type == entity_type)
        if entity_id:
            query = query.where(cls.entity_id == str(entity_id))
        if search:
            like_value = f"%{search}%"
            query = query.where(or_(cls.title.ilike(like_value), cls.message.ilike(like_value)))
        query = query.order_by(cls.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def exists_for_event(cls, db, user_id: str, rule_id: Optional[str], source_event_id: Optional[str]) -> bool:
        if not source_event_id:
            return False
        from sqlalchemy import select
        result = await db.execute(
            select(cls.id).where(
                cls.user_id == str(user_id),
                cls.rule_id == (str(rule_id) if rule_id else None),
                cls.source_event_id == str(source_event_id),
            )
        )
        return result.scalar_one_or_none() is not None

    @classmethod
    async def find_recent(cls, db, user_id: str, rule_id: Optional[str], entity_type: Optional[str], entity_id: Optional[str], since: datetime):
        from sqlalchemy import select
        query = select(cls.id).where(
            cls.user_id == str(user_id),
            cls.rule_id == (str(rule_id) if rule_id else None),
            cls.created_at >= since,
        )
        if entity_type:
            query = query.where(cls.entity_type == entity_type)
        if entity_id:
            query = query.where(cls.entity_id == str(entity_id))
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def mark_read(cls, db, notification_id: str, user_id: str):
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.id == str(notification_id), cls.user_id == str(user_id))
            .values(is_read=True, read_at=datetime.now())
        )
        await db.execute(query)
        await db.commit()

    @classmethod
    async def mark_all_read(cls, db, user_id: str):
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.user_id == str(user_id), cls.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now())
        )
        await db.execute(query)
        await db.commit()
