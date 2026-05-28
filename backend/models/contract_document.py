"""
ContractDocument model - documents within a contract (pdf/edit files).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ContractDocument(Base):
    __tablename__ = "contract_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    doc_type = Column(String(32), nullable=False)
    number_in_contract = Column(Integer, nullable=False)
    status = Column(String(32), default="draft")
    amount = Column(Float)

    pdf_file_name = Column(String(255))
    pdf_storage_path = Column(Text)
    edit_file_name = Column(String(255))
    edit_storage_path = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contract = relationship("Contract", backref="documents")

    @classmethod
    async def get_by_id(cls, db, document_id: str):
        from sqlalchemy import select
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return None
        result = await db.execute(select(cls).where(cls.id == document_uuid))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_contract(cls, db, contract_id: str, doc_type: str = None):
        from sqlalchemy import select
        try:
            contract_uuid = contract_id if isinstance(contract_id, uuid.UUID) else uuid.UUID(str(contract_id))
        except (ValueError, TypeError):
            return []
        query = select(cls).where(cls.contract_id == contract_uuid)
        if doc_type:
            query = query.where(cls.doc_type == doc_type)
        result = await db.execute(query.order_by(cls.doc_type.asc(), cls.number_in_contract.asc()))
        return result.scalars().all()

    @classmethod
    async def get_by_contract_and_type(cls, db, contract_id: str, doc_type: str):
        return await cls.get_by_contract(db, contract_id, doc_type=doc_type)

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        document = cls(**kwargs)
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @classmethod
    async def update(cls, db, document_id: str, **kwargs):
        from sqlalchemy import update
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return None
        query = (
            update(cls)
            .where(cls.id == document_uuid)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, document_id)

    @classmethod
    async def delete(cls, db, document_id: str) -> bool:
        from sqlalchemy import delete
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return False
        result = await db.execute(delete(cls).where(cls.id == document_uuid))
        await db.commit()
        return result.rowcount > 0
