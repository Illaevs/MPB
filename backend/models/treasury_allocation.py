"""
TreasuryAllocation model - распределение транзакции по записям ДДС.
"""
import uuid
from sqlalchemy import Column, Float, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TreasuryAllocation(Base):
    __tablename__ = "treasury_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_transactions.id"), nullable=False)
    income_expense_id = Column(String(36), ForeignKey("income_expense_entries.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category_code = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("TreasuryTransaction")
    income_expense = relationship("IncomeExpenseEntry")

    def __repr__(self):
        return f"<TreasuryAllocation(transaction={self.transaction_id}, entry={self.income_expense_id}, amount={self.amount})>"
