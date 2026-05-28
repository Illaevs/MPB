"""
OutgoingDocumentFile model.
"""
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, or_
from sqlalchemy.sql import func

from app.database.base import Base


class OutgoingDocumentFile(Base):
    __tablename__ = "outgoing_document_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("outgoing_documents.id"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("outgoing_document_versions.id"), nullable=True)
    file_type = Column(String(50), default="attachment")
    file_path = Column(String(500))
    file_name = Column(String(255))
    public_url = Column(String(500))
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
        ).order_by(cls.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        document_file = cls(**kwargs)
        db.add(document_file)
        await db.commit()
        await db.refresh(document_file)
        return document_file
