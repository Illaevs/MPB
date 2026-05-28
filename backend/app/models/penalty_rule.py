"""
Penalty Rule model - Правила штрафов/бонусов для задач
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Float, Boolean, Enum as SqlEnum
from sqlalchemy.sql import func

from app.database.base import Base


class PenaltyRuleType(str, PyEnum):
    RATING = "rating"
    DEADLINE = "deadline"


class PenaltyRule(Base):
    __tablename__ = "penalty_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Тип правила: rating (по оценке) или deadline (по срокам)
    rule_type = Column(SqlEnum("rating", "deadline"), nullable=False)
    
    # Условие: диапазон значений
    # Для rating: condition_min=1, condition_max=1 означает "если оценка = 1"
    # Для deadline: condition_min=-15, condition_max=-100 означает "быстрее на 15%+"
    #               condition_min=10, condition_max=25 означает "опоздание 10-25%"
    condition_min = Column(Float, nullable=False)
    condition_max = Column(Float, nullable=False)
    
    # Коэффициент бюджета
    coefficient = Column(Float, nullable=False, default=1.0)
    
    # Описание правила (для UI)
    description = Column(String(255), nullable=True)
    
    # Активность правила
    is_active = Column(Boolean, default=True)
    
    # Порядок применения (для сортировки)
    sort_order = Column(Float, default=0)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db, only_active: bool = False):
        """Получить все правила"""
        from sqlalchemy import select
        query = select(cls).order_by(cls.rule_type, cls.sort_order)
        if only_active:
            query = query.where(cls.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_type(cls, db, rule_type: str, only_active: bool = True):
        """Получить правила по типу"""
        from sqlalchemy import select
        query = select(cls).where(cls.rule_type == rule_type).order_by(cls.sort_order)
        if only_active:
            query = query.where(cls.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, rule_id: str):
        """Получить правило по ID"""
        from sqlalchemy import select
        query = select(cls).where(cls.id == rule_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новое правило"""
        rule = cls(**kwargs)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @classmethod
    async def update(cls, db, rule_id: str, **kwargs):
        """Обновить правило"""
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.id == rule_id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, rule_id)

    @classmethod
    async def delete(cls, db, rule_id: str) -> bool:
        """Удалить правило"""
        from sqlalchemy import delete
        query = delete(cls).where(cls.id == rule_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @classmethod
    def get_coefficient_for_rating(cls, rating: int, rules: list) -> float:
        """Получить коэффициент для оценки"""
        for rule in rules:
            if rule.condition_min <= rating <= rule.condition_max:
                return rule.coefficient
        return 1.0  # Default

    @classmethod
    def get_coefficient_for_deadline(cls, deviation_percent: float, rules: list) -> float:
        """
        Получить коэффициент для отклонения по срокам.
        deviation_percent: отрицательное = быстрее, положительное = опоздание
        """
        for rule in rules:
            if rule.condition_min <= deviation_percent <= rule.condition_max:
                return rule.coefficient
        return 1.0  # Default

    def __repr__(self):
        return f"<PenaltyRule(id={self.id}, type='{self.rule_type}', coef={self.coefficient})>"
