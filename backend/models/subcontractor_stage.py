"""
SubcontractorStage model - stages for subcontractor cards (Gantt-compatible)
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Date, Integer, Float, JSON, ForeignKey, Enum as SqlEnum, Text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class SubcontractorTermType(str, PyEnum):
    WORK_DAYS = "work_days"
    CALENDAR_DAYS = "calendar_days"
    WEEK = "week"
    MONTH = "month"


class SubcontractorStageStatus(str, PyEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class SubcontractorStage(Base):
    __tablename__ = "subcontractor_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    parent_id = Column(UUID(as_uuid=True), ForeignKey("subcontractor_stages.id"), nullable=True)
    subcontractor_card_id = Column(String(36), ForeignKey("subcontractor_cards.id"), nullable=False)
    contract_id = Column(String(36), ForeignKey("contracts.id"))

    name = Column(String(255), nullable=False)
    description = Column(Text)

    stage_type = Column(SqlEnum("stage", "payment", "other"), default="stage")
    term_type = Column(SqlEnum("work_days", "calendar_days", "week", "month"), default="work_days")

    date_start = Column(Date, nullable=False)
    duration = Column(Integer, nullable=False)
    date_end = Column(Date)
    close_date = Column(Date)

    resources = Column(JSON, default=list)

    planned_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)

    status = Column(SqlEnum("planned", "in_progress", "completed", "delayed"), default="planned")

    subcontractor_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subcontractor_card = relationship("SubcontractorCard", backref="stages")
    contract = relationship("Contract")
    subcontractor = relationship("Company")
    parent = relationship("SubcontractorStage", remote_side=[id], backref="children")
    dependencies = relationship(
        "SubcontractorStageDependency",
        foreign_keys="SubcontractorStageDependency.predecessor_id",
        backref="predecessor"
    )
    dependents = relationship(
        "SubcontractorStageDependency",
        foreign_keys="SubcontractorStageDependency.successor_id",
        backref="successor"
    )

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all (subcontractor stages): {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, stage_id: str):
        from sqlalchemy import select, or_, cast, String
        try:
            stage_uuid = stage_id if isinstance(stage_id, uuid.UUID) else uuid.UUID(str(stage_id))
            variants = [str(stage_uuid), stage_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(stage_id)]
        id_as_text = cast(cls.id, String)
        conditions = [id_as_text == str(value) for value in variants]
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_subcontractor_card_id(cls, db, card_id: str):
        from sqlalchemy import select, or_
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
        except (ValueError, TypeError):
            card_uuid = None
        card_id_str = str(card_uuid) if card_uuid else str(card_id)
        card_id_hex = card_uuid.hex if card_uuid else None
        conditions = [cls.subcontractor_card_id == card_id_str]
        if card_id_hex:
            conditions.append(cls.subcontractor_card_id == card_id_hex)
        query = select(cls).where(or_(*conditions)).order_by(cls.date_start)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        for key in ("subcontractor_card_id", "contract_id", "parent_id", "subcontractor_id", "id"):
            if key in kwargs and isinstance(kwargs[key], uuid.UUID):
                kwargs[key] = str(kwargs[key])
        stage = cls(**kwargs)
        db.add(stage)
        await db.commit()
        await db.refresh(stage)
        return stage

    @classmethod
    async def update(cls, db, stage_id: str, **kwargs):
        from sqlalchemy import update, or_, cast, String
        try:
            stage_uuid = stage_id if isinstance(stage_id, uuid.UUID) else uuid.UUID(str(stage_id))
            variants = [str(stage_uuid), stage_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(stage_id)]
        for key in ("subcontractor_card_id", "contract_id", "parent_id", "subcontractor_id"):
            if key in kwargs and isinstance(kwargs[key], uuid.UUID):
                kwargs[key] = str(kwargs[key])
        id_as_text = cast(cls.id, String)
        conditions = [id_as_text == str(value) for value in variants]
        query = (
            update(cls)
            .where(or_(*conditions))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, stage_id)

    @classmethod
    async def delete(cls, db, stage_id: str) -> bool:
        from sqlalchemy import delete, or_, cast, String
        try:
            stage_uuid = stage_id if isinstance(stage_id, uuid.UUID) else uuid.UUID(str(stage_id))
            variants = [str(stage_uuid), stage_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(stage_id)]
        id_as_text = cast(cls.id, String)
        conditions = [id_as_text == str(value) for value in variants]
        query = delete(cls).where(or_(*conditions))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<SubcontractorStage(id={self.id}, name='{self.name}', start={self.date_start})>"

