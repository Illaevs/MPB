"""
RolePermission model - section permissions for roles.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    section = Column(String(64), nullable=False)
    read_all = Column(Boolean, default=False)
    read_assigned = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("Role", backref="permissions")

    @classmethod
    async def get_by_role(cls, db, role_id: str):
        from sqlalchemy import select
        try:
            role_uuid = role_id if isinstance(role_id, uuid.UUID) else uuid.UUID(str(role_id))
        except (ValueError, TypeError):
            role_uuid = None
        role_id_str = str(role_uuid) if role_uuid else str(role_id)
        result = await db.execute(select(cls).where(cls.role_id == role_id_str))
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        permission = cls(**kwargs)
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission
