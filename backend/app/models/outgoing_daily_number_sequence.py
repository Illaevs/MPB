"""
Daily numbering counters for financial outgoing documents.
"""
from sqlalchemy import Column, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class OutgoingDailyNumberSequence(Base):
    __tablename__ = "outgoing_daily_number_sequences"
    __table_args__ = (
        UniqueConstraint(
            "our_company_key",
            "document_kind",
            "sequence_date",
            name="uq_outgoing_daily_number_sequence_scope",
        ),
    )

    id = Column(String(36), primary_key=True)
    our_company_key = Column(String(32), nullable=False, index=True)
    document_kind = Column(String(32), nullable=False, index=True)
    sequence_date = Column(Date, nullable=False, index=True)
    next_seq = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
