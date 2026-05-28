"""
Stage model - Этапы работ (Gantt chart)
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Date, Integer, Float, JSON, ForeignKey, Enum as SqlEnum, Text, Boolean, or_, cast
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TermType(str, PyEnum):
    WORK_DAYS = "work_days"      # Рабочие дни
    CALENDAR_DAYS = "calendar_days"  # Calendar days
    WEEK = "week"  # Weeks
    MONTH = "month"  # Months


class StageStatus(str, PyEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"


class Stage(Base):
    __tablename__ = "stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Иерархия (рекурсивная связь)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)

    # Основная информация
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Тип этапа
    stage_type = Column(SqlEnum("stage", "payment", "other"), default="stage")
    term_type = Column(SqlEnum("work_days", "calendar_days", "week", "month"), default="work_days")

    # Временные параметры
    date_start = Column(Date, nullable=False)
    duration = Column(Integer, nullable=False)  # в днях
    date_end = Column(Date)  # вычисляемое поле
    close_date = Column(Date)

    # Ресурсы и материалы (JSONB)
    resources = Column(JSON, default=list)  # массив материалов и работ

    # Финансовая информация
    planned_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)

    # Статус
    status = Column(SqlEnum("planned", "in_progress", "completed", "delayed"), default="planned")
    is_closed = Column(Boolean, default=False)

    # Ответственный подрядчик
    subcontractor_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    deal = relationship("Deal", backref="stages")
    subcontractor = relationship("Company")
    parent = relationship("Stage", remote_side=[id], backref="children")
    dependencies = relationship("StageDependency", foreign_keys="StageDependency.predecessor_id", backref="predecessor")
    dependents = relationship("StageDependency", foreign_keys="StageDependency.successor_id", backref="successor")

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        """Получить все этапы"""
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, stage_id: str):
        """Получить этап по ID"""
        from sqlalchemy import select
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
    async def get_by_deal_id(cls, db, deal_id: str):
        """Получить все этапы проекта"""
        from sqlalchemy import select
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
            variants = [str(deal_uuid), deal_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(deal_id)]
        deal_as_text = cast(cls.deal_id, String)
        conditions = [deal_as_text == str(value) for value in variants]
        query = select(cls).where(or_(*conditions)).order_by(cls.date_start)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новый этап"""
        from datetime import datetime
        # Set created_at and updated_at explicitly
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        stage = cls(**kwargs)
        db.add(stage)
        await db.commit()
        await db.refresh(stage)
        return stage

    @classmethod
    async def update(cls, db, stage_id: str, **kwargs):
        """Обновить этап"""
        from sqlalchemy import update
        try:
            stage_uuid = stage_id if isinstance(stage_id, uuid.UUID) else uuid.UUID(str(stage_id))
            variants = [str(stage_uuid), stage_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(stage_id)]
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

        # Получить обновленный объект
        return await cls.get_by_id(db, stage_id)

    @classmethod
    async def delete(cls, db, stage_id: str) -> bool:
        """Удалить этап"""
        from sqlalchemy import delete
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
        return f"<Stage(id={self.id}, name='{self.name}', start={self.date_start})>"

