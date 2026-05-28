import uuid
from datetime import datetime

from sqlalchemy import Column, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class AdvancePayment(Base):
    __tablename__ = "advance_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(UUID(as_uuid=True), nullable=True)
    contract_id = Column(UUID(as_uuid=True), nullable=True)
    amount_total = Column(Float, default=0.0)
    vat_rate = Column(Float, default=20.0)
    remaining_total = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
