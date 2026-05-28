"""
StageProductLink model - many-to-many between deal stages and deal products.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class StageProductLink(Base):
    __tablename__ = "stage_product_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=False)
    stage_id = Column(String(36), ForeignKey("stages.id"), nullable=False)
    deal_product_id = Column(String(36), ForeignKey("deal_products.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deal = relationship("Deal")
    stage = relationship("Stage")
    deal_product = relationship("DealProduct")

    @classmethod
    def _id_conditions(cls, column, value):
        variants = []
        try:
            parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
            variants.extend([parsed, str(parsed), parsed.hex])
        except (ValueError, TypeError):
            variants.append(str(value))
        return or_(*[column == v for v in variants])

    @classmethod
    async def get_by_deal(cls, db, deal_id: str):
        from sqlalchemy import select
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            return []
        query = select(cls).where(
            or_(cls.deal_id == deal_uuid, cls.deal_id == str(deal_uuid), cls.deal_id == deal_uuid.hex)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_stage(cls, db, stage_id: str):
        from sqlalchemy import select
        query = select(cls).where(cls._id_conditions(cls.stage_id, stage_id))
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        kwargs["created_at"] = datetime.now()
        bind = db.get_bind()
        is_sqlite = bool(bind and bind.dialect.name == "sqlite")
        if is_sqlite:
            for key in ("deal_id", "stage_id"):
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
    async def delete_by_stage(cls, db, stage_id: str):
        from sqlalchemy import delete
        query = delete(cls).where(cls._id_conditions(cls.stage_id, stage_id))
        await db.execute(query)
        await db.commit()
