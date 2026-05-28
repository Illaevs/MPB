"""
TransactionAllocation model - Распределение платежей по статьям плана
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TransactionAllocation(Base):
    __tablename__ = "transaction_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Ссылка на транзакцию
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_transactions.id"), nullable=False)

    # Ссылка на плановую запись
    financial_plan_id = Column(UUID(as_uuid=True), ForeignKey("financial_plans.id"), nullable=False)

    # Распределенная сумма
    amount = Column(Float, nullable=False)

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    transaction = relationship("TreasuryTransaction")
    financial_plan = relationship("FinancialPlan")

    def __repr__(self):
        return f"<TransactionAllocation(transaction={self.transaction_id}, plan={self.financial_plan_id}, amount={self.amount})>"
