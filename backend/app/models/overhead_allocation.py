import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class OverheadAllocation(Base):
    __tablename__ = "overhead_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    period = Column(String(7), nullable=False)  # YYYY-MM
    amount = Column(Float, default=0.0)
    calc_version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_by_period(cls, db, period: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.period == period))
        return result.scalars().all()

    @classmethod
    async def get_by_deal(cls, db, deal_id: uuid.UUID):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.deal_id == deal_id))
        return result.scalars().all()

    @classmethod
    async def delete_by_period(cls, db, period: str):
        from sqlalchemy import delete
        result = await db.execute(delete(cls).where(cls.period == period))
        await db.commit()
        return result.rowcount
