import uuid
from datetime import datetime, date

from sqlalchemy import Column, Float, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class PricingQuote(Base):
    __tablename__ = "pricing_quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    model_id = Column(UUID(as_uuid=True), nullable=True)
    calc_date = Column(Date, nullable=False)
    base_cost = Column(Float, default=0.0)
    overheads = Column(Float, default=0.0)
    indexed_cost = Column(Float, default=0.0)
    risk = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    final_price = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
