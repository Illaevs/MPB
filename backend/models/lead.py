"""
Lead model - входящие заявки до конверсии в сделку.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String(255), nullable=False)
    obj_name = Column(String(500))
    address = Column(Text)
    object_type = Column(String(100))
    object_area = Column(Float)

    customer_id = Column(String(36), ForeignKey("companies.id"))
    our_company_id = Column(String(36), ForeignKey("companies.id"))
    responsible_user_id = Column(String(36), ForeignKey("users.id"))

    advance_percent = Column(Float, default=0.0)
    vat_rate = Column(Float, default=20.0)
    status = Column(String(50), default="incoming")
    total_value = Column(Float, default=0.0)

    deal_id = Column(String(36), ForeignKey("deals.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Company", foreign_keys=[customer_id])
    our_company = relationship("Company", foreign_keys=[our_company_id])
    responsible_user = relationship("User", foreign_keys=[responsible_user_id])
    deal = relationship("Deal", foreign_keys=[deal_id])

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        query = select(cls).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_filtered(
        cls,
        db,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        responsible_user_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        our_company_id: Optional[str] = None,
    ):
        from sqlalchemy import select, and_, or_
        query = select(cls)
        filters = []

        def id_filter_values(value):
            text = str(value or "").strip()
            if not text:
                return []
            compact = text.replace("-", "").lower()
            values = {text, compact}
            if len(compact) == 32:
                values.add(
                    f"{compact[0:8]}-{compact[8:12]}-{compact[12:16]}-"
                    f"{compact[16:20]}-{compact[20:32]}"
                )
            return list(values)

        if status:
            filters.append(cls.status == status)
        if responsible_user_id:
            filters.append(cls.responsible_user_id == responsible_user_id)
        customer_values = id_filter_values(customer_id)
        if customer_values:
            filters.append(cls.customer_id.in_(customer_values))
        our_company_values = id_filter_values(our_company_id)
        if our_company_values:
            filters.append(cls.our_company_id.in_(our_company_values))
        if search and search.strip():
            token = f"%{search.strip()}%"
            filters.append(or_(cls.title.ilike(token), cls.obj_name.ilike(token), cls.address.ilike(token)))
        if filters:
            query = query.where(and_(*filters))
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, lead_id: str):
        from sqlalchemy import select, or_
        try:
            lead_uuid = lead_id if isinstance(lead_id, uuid.UUID) else uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            lead_uuid = None
        lead_id_str = str(lead_uuid) if lead_uuid else str(lead_id)
        lead_id_hex = lead_uuid.hex if lead_uuid else None
        conditions = [cls.id == lead_id_str]
        if lead_id_hex:
            conditions.append(cls.id == lead_id_hex)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        for key in ("customer_id", "our_company_id", "deal_id", "responsible_user_id"):
            value = kwargs.get(key)
            if isinstance(value, uuid.UUID):
                kwargs[key] = str(value)
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def update(cls, db, lead_id: str, **kwargs):
        from sqlalchemy import update, or_
        try:
            lead_uuid = lead_id if isinstance(lead_id, uuid.UUID) else uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            return None

        processed = {}
        for key, value in kwargs.items():
            if key in ("customer_id", "our_company_id", "deal_id", "responsible_user_id") and isinstance(value, uuid.UUID):
                processed[key] = str(value)
            else:
                processed[key] = value

        processed["updated_at"] = datetime.now()
        lead_id_str = str(lead_uuid)
        lead_id_hex = lead_uuid.hex
        query = (
            update(cls)
            .where(or_(cls.id == lead_uuid, cls.id == lead_id_str, cls.id == lead_id_hex))
            .values(**processed)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, lead_id)

    @classmethod
    async def delete(cls, db, lead_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            lead_uuid = lead_id if isinstance(lead_id, uuid.UUID) else uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            return False
        lead_id_str = str(lead_uuid)
        lead_id_hex = lead_uuid.hex
        query = delete(cls).where(or_(cls.id == lead_uuid, cls.id == lead_id_str, cls.id == lead_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @classmethod
    async def calculate_total_value(cls, db, lead_id: str):
        from sqlalchemy import select, func, or_
        try:
            lead_uuid = lead_id if isinstance(lead_id, uuid.UUID) else uuid.UUID(str(lead_id))
            lead_id_str = str(lead_uuid)
            lead_id_hex = lead_uuid.hex
        except Exception as exc:
            lead_uuid = None
            lead_id_str = str(lead_id)
            lead_id_hex = None
            print(f"Error calculating total value for lead {lead_id}: {exc}")
            return 0.0

        from app.models.lead_product import LeadProduct
        query = select(func.sum(LeadProduct.final_price)).where(
            or_(
                LeadProduct.lead_id == lead_uuid,
                LeadProduct.lead_id == lead_id_str,
                LeadProduct.lead_id == lead_id_hex,
            )
        )
        result = await db.execute(query)
        total = result.scalar() or 0.0
        await cls.update(db, lead_id, total_value=total)
        return total
