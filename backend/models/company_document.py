"""
CompanyDocument model - accreditation documents with moderation.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.sql import func

from app.database.base import Base


class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    our_company_id = Column(String(36), ForeignKey("companies.id"), nullable=True, index=True)
    doc_type = Column(String(50), nullable=False)  # portfolio, diploma, license, sro
    doc_value = Column(String(255))  # e.g. SRO level or other metadata
    file_name = Column(String(255))
    file_url = Column(Text)
    storage_path = Column(Text)
    file_size = Column(Integer)
    content_type = Column(String(255))
    parent_id = Column(String(36), ForeignKey("company_documents.id"))

    status = Column(String(20), default="pending")  # pending, approved, rejected
    comment = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CompanyDocument(company={self.company_id}, type={self.doc_type}, status={self.status})>"
