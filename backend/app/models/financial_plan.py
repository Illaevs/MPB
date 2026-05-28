"""
FinancialPlan model - Плановые финансовые операции
"""
import uuid
from datetime import datetime, date
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Date, Float, ForeignKey, Enum as SqlEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class PaymentStatus(str, PyEnum):
    UNPAID = "unpaid"      # Не оплачено
    PARTIAL = "partial"    # Частично оплачено
    PAID = "paid"          # Полностью оплачено


class FinancialPlan(Base):
    __tablename__ = "financial_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Связь с проектом
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)

    # Направление (доход/расход)
    direction = Column(SqlEnum("income", "expense"), nullable=False)

    # Суммы
    amount_plan = Column(Float, nullable=False)

    # Даты
    date_plan_start = Column(Date)
    date_plan_end = Column(Date)

    # Описание
    description = Column(Text)

    # Контрагент (для расходов - подрядчик, для доходов - заказчик)
    contractor_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))

    # Связь с договором субподряда (если применимо)
    subcontractor_contract_id = Column(String(255))  # Номер договора

    # Статус оплаты
    payment_status = Column(SqlEnum("unpaid", "partial", "paid"), default="unpaid")

    # Связь с этапом (если платеж привязан к этапу)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"))

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    deal = relationship("Deal")
    contractor = relationship("Company")
    stage = relationship("Stage")

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        """Получить все финансовые планы"""
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, plan_id: str):
        """Получить финансовый план по ID"""
        from sqlalchemy import select
        try:
            plan_uuid = plan_id if isinstance(plan_id, uuid.UUID) else uuid.UUID(str(plan_id))
        except (ValueError, TypeError):
            return None
        query = select(cls).where(cls.id == plan_uuid)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_deal_id(cls, db, deal_id: str):
        """Получить все финансовые планы проекта"""
        from sqlalchemy import select
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            return []
        query = select(cls).where(cls.deal_id == deal_uuid).order_by(cls.date_plan_start)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новый финансовый план"""
        from datetime import datetime
        # Set created_at and updated_at explicitly
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        plan = cls(**kwargs)
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @classmethod
    async def update(cls, db, plan_id: str, **kwargs):
        """Обновить финансовый план"""
        from sqlalchemy import update
        try:
            plan_uuid = plan_id if isinstance(plan_id, uuid.UUID) else uuid.UUID(str(plan_id))
        except (ValueError, TypeError):
            return None
        query = (
            update(cls)
            .where(cls.id == plan_uuid)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()

        # Получить обновленный объект
        return await cls.get_by_id(db, plan_id)

    @classmethod
    async def delete(cls, db, plan_id: str) -> bool:
        """Удалить финансовый план"""
        from sqlalchemy import delete
        try:
            plan_uuid = plan_id if isinstance(plan_id, uuid.UUID) else uuid.UUID(str(plan_id))
        except (ValueError, TypeError):
            return False
        query = delete(cls).where(cls.id == plan_uuid)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<FinancialPlan(id={self.id}, direction={self.direction}, amount={self.amount_plan})>"
