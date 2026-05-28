import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class WipMonthly(Base):
    __tablename__ = "wip_monthly"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    stage_id = Column(UUID(as_uuid=True), nullable=False)
    period = Column(String(7), nullable=False)  # YYYY-MM
    base_amount = Column(Float, default=0.0)
    vat_rate = Column(Float, default=20.0)
    vat_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    is_forecast = Column(Boolean, default=True)
    calc_version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_by_deal(cls, db, deal_id: uuid.UUID):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.deal_id == deal_id).order_by(cls.period))
        return result.scalars().all()
