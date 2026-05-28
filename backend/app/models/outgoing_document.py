"""
OutgoingDocument model.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Date, Text, DateTime, ForeignKey, Integer, UniqueConstraint, or_
from sqlalchemy.sql import func

from app.database.base import Base


class OutgoingDocument(Base):
    __tablename__ = "outgoing_documents"
    __table_args__ = (
        UniqueConstraint("outgoing_number", name="uq_outgoing_documents_number"),
        UniqueConstraint("outgoing_number_seq", name="uq_outgoing_documents_seq"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    outgoing_number_seq = Column(Integer, nullable=False, index=True)
    outgoing_number = Column(String(50), nullable=False, index=True)
    document_kind = Column(String(32), nullable=False, default="letter", index=True)
    our_company_key = Column(String(32))
    outgoing_number_company_seq = Column(Integer)
    recipient_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=True)
    contract_id = Column(String(36), nullable=True, index=True)
    letter_date = Column(Date, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, default="")
    attachments_list = Column(Text)
    bank_account_index = Column(Integer)
    bank_account_snapshot = Column(Text)
    linked_stage_ids = Column(Text)
    linked_payment_items = Column(Text)
    act_contract_document_id = Column(String(36), nullable=True)
    recipient_short_name = Column(String(255))
    recipient_to_name = Column(String(255))
    recipient_appeal = Column(String(255))
    recipient_eio = Column(String(255))
    recipient_genitive_name = Column(String(255))
    recipient_salutation = Column(String(32))
    editor_mode = Column(String(32), default="classic")
    editor_schema_version = Column(Integer, default=1)
    editor_draft_json = Column(Text)
    editor_validation_json = Column(Text)
    editor_render_context_json = Column(Text)
    status = Column(String(50), default="draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        query = select(cls).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, document_id: str):
        from sqlalchemy import select
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return None
        document_id_str = str(document_uuid)
        document_id_hex = document_uuid.hex
        query = select(cls).where(or_(cls.id == document_id_str, cls.id == document_id_hex, cls.id == str(document_id)))
        result = await db.execute(query)
        return result.scalar_one_or_none()

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
        from sqlalchemy import update, or_
        try:
            document_uuid = document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
        except (ValueError, TypeError):
            return None
        document_id_str = str(document_uuid)
        document_id_hex = document_uuid.hex

        processed_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, uuid.UUID):
                processed_kwargs[key] = str(value)
            else:
                processed_kwargs[key] = value

        query = (
            update(cls)
            .where(or_(cls.id == document_id_str, cls.id == document_id_hex))
            .values(**processed_kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, document_id)
