"""
SubcontractorCard model - карточки субподрядчиков (логика как у сделок)
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class SubcontractorCard(Base):
    __tablename__ = "subcontractor_cards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String(255), nullable=False)
    obj_name = Column(String(500))
    address = Column(Text)
    object_type = Column(String(100))
    object_area = Column(Float)

    company_id = Column(String(36), ForeignKey("companies.id"))

    customer_id = Column(String(36), ForeignKey("companies.id"))
    general_contractor_id = Column(String(36), ForeignKey("companies.id"))

    penalty_config = Column(JSON, default=dict)

    s3_prefix_tz = Column(String(500))
    s3_prefix_docs = Column(String(500))

    status = Column(String(50), default="active")

    total_contract_value = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)

    vat_rate = Column(Float, default=20.0)
    vat_included = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", foreign_keys=[company_id])
    customer = relationship("Company", foreign_keys=[customer_id])
    general_contractor = relationship("Company", foreign_keys=[general_contractor_id])

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all (subcontractors): {e}")
            return []

    @classmethod
    async def get_filtered(
        cls,
        db,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        min_contract_value: Optional[float] = None,
        max_contract_value: Optional[float] = None,
        search: Optional[str] = None
    ):
        from sqlalchemy import select, and_, or_
        try:
            query = select(cls)
            filters = []

            if status:
                filters.append(cls.status == status)

            if min_contract_value is not None:
                filters.append(cls.total_contract_value >= min_contract_value)
            if max_contract_value is not None:
                filters.append(cls.total_contract_value <= max_contract_value)

            if search and search.strip():
                search_term = f"%{search.strip()}%"
                search_filters = [
                    cls.title.ilike(search_term),
                    cls.obj_name.ilike(search_term),
                    cls.address.ilike(search_term)
                ]
                filters.append(or_(*search_filters))

            if filters:
                query = query.where(and_(*filters))

            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_filtered (subcontractors): {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, card_id: str):
        from sqlalchemy import select, or_
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
        except (ValueError, TypeError):
            card_uuid = None
        card_id_str = str(card_uuid) if card_uuid else str(card_id)
        card_id_hex = card_uuid.hex if card_uuid else None
        conditions = [cls.id == card_id_str]
        if card_id_hex:
            conditions.append(cls.id == card_id_hex)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        for key in ("company_id", "customer_id", "general_contractor_id"):
            value = kwargs.get(key)
            if isinstance(value, uuid.UUID):
                kwargs[key] = str(value)
        card = cls(**kwargs)
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    @classmethod
    async def update(cls, db, card_id: str, **kwargs):
        from sqlalchemy import update, or_
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
        except (ValueError, TypeError):
            card_uuid = None

        processed_kwargs = {}
        for key, value in kwargs.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                try:
                    processed_kwargs[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
            else:
                processed_kwargs[key] = value

        processed_kwargs['updated_at'] = datetime.now()

        card_id_str = str(card_uuid) if card_uuid else str(card_id)
        card_id_hex = card_uuid.hex if card_uuid else None
        conditions = [cls.id == card_id_str]
        if card_id_hex:
            conditions.append(cls.id == card_id_hex)

        query = (
            update(cls)
            .where(or_(*conditions))
            .values(**processed_kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, card_id)

    @classmethod
    async def delete(cls, db, card_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
        except (ValueError, TypeError):
            card_uuid = None
        card_id_str = str(card_uuid) if card_uuid else str(card_id)
        card_id_hex = card_uuid.hex if card_uuid else None
        conditions = [cls.id == card_id_str]
        if card_id_hex:
            conditions.append(cls.id == card_id_hex)
        query = delete(cls).where(or_(*conditions))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<SubcontractorCard(id={self.id}, title='{self.title}')>"
