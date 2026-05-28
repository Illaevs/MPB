import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class InflationIndex(Base):
    __tablename__ = "inflation_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String(7), nullable=False)  # YYYY-MM
    value = Column(Float, default=1.0)
    note = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 200):
        from sqlalchemy import select
        query = select(cls).offset(skip).limit(limit).order_by(cls.period)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_period(cls, db, period: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.period == period))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def update(cls, db, item_id: str, **kwargs):
        from sqlalchemy import update
        item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        query = update(cls).where(cls.id == item_uuid).values(**kwargs)
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, item_id)

    @classmethod
    async def get_by_id(cls, db, item_id: str):
        from sqlalchemy import select
        item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        result = await db.execute(select(cls).where(cls.id == item_uuid))
        return result.scalar_one_or_none()

    @classmethod
    async def delete(cls, db, item_id: str) -> bool:
        from sqlalchemy import delete
        item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        result = await db.execute(delete(cls).where(cls.id == item_uuid))
        await db.commit()
        return result.rowcount > 0
