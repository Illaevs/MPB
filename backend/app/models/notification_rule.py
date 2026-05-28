"""
Notification rule model for in-app alerts engine.
"""
import uuid
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.sql import func

from app.database.base import Base


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    trigger = Column(String(64), nullable=False)
    entity_type = Column(String(64))
    priority = Column(String(16), default="info")
    audience_type = Column(String(32), default="assigned_user")
    audience_value = Column(String(64))
    require_subscription = Column(Boolean, default=False)
    conditions = Column(JSON, default=dict)
    quiet_policy = Column(String(16), default="respect")
    deliver_in_app = Column(Boolean, default=True)
    deliver_telegram = Column(Boolean, default=False)
    throttle_minutes = Column(Integer, default=0)
    title_template = Column(String(255))
    message_template = Column(Text)
    action_url_template = Column(String(255))
    created_by = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_active_for_trigger(cls, db, trigger: str):
        from sqlalchemy import select
        result = await db.execute(
            select(cls).where(cls.is_active.is_(True), cls.trigger == trigger)
        )
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, rule_id: str) -> Optional["NotificationRule"]:
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(rule_id)))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        rule = cls(**kwargs)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @classmethod
    async def update(cls, db, rule_id: str, **kwargs):
        from sqlalchemy import update
        await db.execute(
            update(cls)
            .where(cls.id == str(rule_id))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.commit()
        return await cls.get_by_id(db, rule_id)
