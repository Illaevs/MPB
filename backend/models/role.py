"""
Role model - user roles.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.database.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(80), nullable=False, unique=True)
    description = Column(String(255))
    is_system = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db):
        from sqlalchemy import select
        result = await db.execute(select(cls).order_by(cls.name))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, role_id: str):
        from sqlalchemy import select
        try:
            role_uuid = role_id if isinstance(role_id, uuid.UUID) else uuid.UUID(str(role_id))
        except (ValueError, TypeError):
            role_uuid = None
        role_id_str = str(role_uuid) if role_uuid else str(role_id)
        result = await db.execute(select(cls).where(cls.id == role_id_str))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_name(cls, db, name: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.name == name))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        role = cls(**kwargs)
        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    @classmethod
    async def update(cls, db, role_id: str, **kwargs):
        from sqlalchemy import update
        try:
            role_uuid = role_id if isinstance(role_id, uuid.UUID) else uuid.UUID(str(role_id))
        except (ValueError, TypeError):
            role_uuid = None
        role_id_str = str(role_uuid) if role_uuid else str(role_id)
        query = (
            update(cls)
            .where(cls.id == role_id_str)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, role_id)

    @classmethod
    async def delete(cls, db, role_id: str) -> bool:
        from sqlalchemy import delete
        try:
            role_uuid = role_id if isinstance(role_id, uuid.UUID) else uuid.UUID(str(role_id))
        except (ValueError, TypeError):
            role_uuid = None
        role_id_str = str(role_uuid) if role_uuid else str(role_id)
        result = await db.execute(delete(cls).where(cls.id == role_id_str))
        await db.commit()
        return result.rowcount > 0
