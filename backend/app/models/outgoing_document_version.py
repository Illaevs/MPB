"""
OutgoingDocumentVersion model.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, or_
from sqlalchemy.sql import func

from app.database.base import Base


class OutgoingDocumentVersion(Base):
    __tablename__ = "outgoing_document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("outgoing_documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), default="draft")
    created_by = Column(String(255))
    comment = Column(Text)
    pdf_path = Column(String(500))
    pdf_public_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def get_by_document(cls, db, document_id: str):
        from sqlalchemy import select
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return []
        document_id_str = str(document_uuid)
        document_id_hex = document_uuid.hex
        query = select(cls).where(
            or_(cls.document_id == document_id_str, cls.document_id == document_id_hex, cls.document_id == str(document_id))
        ).order_by(cls.version_number.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        document_version = cls(**kwargs)
        db.add(document_version)
        await db.commit()
        await db.refresh(document_version)
        return document_version
