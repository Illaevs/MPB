"""
CompanyAccreditation model - company accreditation by direction.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class CompanyAccreditation(Base):
    __tablename__ = "company_accreditations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    direction_id = Column(String(36), nullable=False)  # product category id

    status = Column(String(20), default="pending")  # pending, approved, rejected
    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CompanyAccreditation(company={self.company_id}, direction={self.direction_id}, status={self.status})>"
