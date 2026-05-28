"""
StageProductAssignment model - links deal stages, products, and subcontractors.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class StageProductAssignment(Base):
    __tablename__ = "stage_product_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=False)
    stage_id = Column(String(36), ForeignKey("stages.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    subcontractor_card_id = Column(String(36), ForeignKey("subcontractor_cards.id"), nullable=False)
    subcontractor_product_id = Column(String(36), ForeignKey("subcontractor_products.id"))
    contract_id = Column(String(36), ForeignKey("contracts.id"))

    start_date = Column(Date)
    due_date = Column(Date)
    contract_due_date = Column(Date)
    status = Column(String(50), default="not_started")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    deal = relationship("Deal")
    stage = relationship("Stage")
    product = relationship("Product")
    subcontractor_card = relationship("SubcontractorCard")
    subcontractor_product = relationship("SubcontractorProduct")
    contract = relationship("Contract")

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        bind = db.get_bind()
        is_sqlite = bool(bind and bind.dialect.name == "sqlite")
        if is_sqlite:
            for key in ("deal_id", "stage_id", "product_id", "contract_id"):
                if key in kwargs and kwargs[key] is not None:
                    try:
                        u = kwargs[key] if isinstance(kwargs[key], uuid.UUID) else uuid.UUID(str(kwargs[key]))
                        kwargs[key] = u.hex
                    except (ValueError, TypeError):
                        pass
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def update(cls, db, item_id: str, **kwargs):
        from sqlalchemy import update, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return None
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        kwargs["updated_at"] = datetime.now()
        query = (
            update(cls)
            .where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, item_id)

    @classmethod
    async def get_by_id(cls, db, item_id: str):
        from sqlalchemy import select, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return None
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = select(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def delete(cls, db, item_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return False
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = delete(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
