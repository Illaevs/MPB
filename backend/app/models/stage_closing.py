import uuid
from datetime import datetime, date

from sqlalchemy import Column, Float, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class StageClosing(Base):
    __tablename__ = "stage_closings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id = Column(UUID(as_uuid=True), nullable=False)
    deal_id = Column(UUID(as_uuid=True), nullable=False)
    contract_id = Column(UUID(as_uuid=True), nullable=True)
    closing_date = Column(Date, nullable=False)
    base_amount = Column(Float, default=0.0)
    vat_rate = Column(Float, default=20.0)
    vat_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    advance_covered_base = Column(Float, default=0.0)
    advance_covered_vat = Column(Float, default=0.0)
    remaining_base = Column(Float, default=0.0)
    remaining_vat = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
