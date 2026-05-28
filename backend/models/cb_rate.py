"""
CBRate model - Ставки Центрального банка для расчета PV
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, DateTime, Date, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class CBRate(Base):
    __tablename__ = "cb_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Дата действия ставки
    rate_date = Column(Date, nullable=False, unique=True, index=True)

    # Значение ставки в процентах
    rate_value = Column(Float, nullable=False)

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CBRate(date={self.rate_date}, rate={self.rate_value}%)>"
