"""
StageResult model - history of uploaded results for subcontractor stages.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.sql import func

from app.database.base import Base


class StageResult(Base):
    __tablename__ = "stage_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    stage_id = Column(String(36), ForeignKey("subcontractor_stages.id"), nullable=False)
    subcontractor_card_id = Column(String(36), ForeignKey("subcontractor_cards.id"), nullable=False)
    deal_id = Column(String(36), ForeignKey("deals.id"))

    product_name = Column(String(255), nullable=False)
    version_label = Column(String(50), nullable=False)
    version_number = Column(Integer, nullable=True)

    comment = Column(Text)
    reviewer_comment = Column(Text)
    status = Column(String(50), default="review")
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    storage_path = Column(Text, nullable=False)
    public_url = Column(Text)
    created_by = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_by_stage(cls, db, stage_id: str):
        from sqlalchemy import select, or_
        query = select(cls).where(or_(cls.stage_id == stage_id, cls.stage_id == str(stage_id))).order_by(cls.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, result_id: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(result_id)))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs.setdefault("updated_at", now)
        kwargs.setdefault("status", "review")
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def update(cls, db, result_id: str, **kwargs):
        from sqlalchemy import update
        kwargs["updated_at"] = datetime.now()
        query = (
            update(cls)
            .where(cls.id == str(result_id))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, result_id)

    @classmethod
    async def delete(cls, db, result_id: str) -> bool:
        from sqlalchemy import delete
        result = await db.execute(delete(cls).where(cls.id == str(result_id)))
        await db.commit()
        return result.rowcount > 0
