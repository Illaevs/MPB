"""
OutgoingNumberSequence model.
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class OutgoingNumberSequence(Base):
    __tablename__ = "outgoing_number_sequences"

    our_company_key = Column(String(32), primary_key=True)
    next_seq = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
