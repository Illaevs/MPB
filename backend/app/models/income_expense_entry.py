"""
IncomeExpenseEntry model - Income/Expense registry entries.
"""
import uuid
from sqlalchemy import Column, String, Date, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class IncomeExpenseEntry(Base):
    __tablename__ = "income_expense_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    direction = Column(String(10), nullable=False)  # income / expense
    amount = Column(Float, nullable=False)

    plan_date = Column(Date, nullable=False)
    actual_date = Column(Date)

    payer_id = Column(String(36), ForeignKey("companies.id"))
    payee_id = Column(String(36), ForeignKey("companies.id"))
    deal_id = Column(String(36), ForeignKey("deals.id"))
    contract_id = Column(String(36), ForeignKey("contracts.id"))
    stage_id = Column(String(36), ForeignKey("stages.id"))  # Link to payment stage
    category_code = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<IncomeExpenseEntry(id={self.id}, direction={self.direction}, amount={self.amount})>"
