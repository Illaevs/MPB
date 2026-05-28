"""
TenderOffer model - invitations and responses from subcontractors.
"""
import uuid
from sqlalchemy import Column, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class TenderOffer(Base):
    __tablename__ = "tender_offers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    tender_id = Column(String(36), ForeignKey("tenders.id"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)

    status = Column(String(20), default="invited")  # invited, responded, rejected, winner
    proposed_amount = Column(Float)
    proposed_deadline = Column(Date)
    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TenderOffer(id={self.id}, tender_id={self.tender_id}, status={self.status})>"
