"""
StageProductSubtask model - subtasks for stage product assignments.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class StageProductSubtask(Base):
    __tablename__ = "stage_product_subtasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String(36), ForeignKey("stage_product_assignments.id"), nullable=False)

    title = Column(String(255), nullable=False)
    due_date = Column(Date)
    status = Column(String(50), default="not_started")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assignment = relationship("StageProductAssignment", backref="subtasks")

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        assignment_id = kwargs.get("assignment_id")
        if isinstance(assignment_id, uuid.UUID):
            kwargs["assignment_id"] = str(assignment_id)
        item = cls(**kwargs)
        db.add(item)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        return item

    @classmethod
    async def update(cls, db, item_id: str, **kwargs):
        from sqlalchemy import update, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return None
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        kwargs["updated_at"] = datetime.now()
        query = (
            update(cls)
            .where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, item_id)

    @classmethod
    async def get_by_id(cls, db, item_id: str):
        from sqlalchemy import select, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return None
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = select(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def delete(cls, db, item_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return False
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = delete(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
