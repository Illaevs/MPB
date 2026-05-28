from typing import Optional, Union, List
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, field_serializer

from app.schemas.treasury_allocation import TreasuryAllocationResponse


class TreasuryTransactionBase(BaseModel):
    doc_num: str
    transaction_date: date
    amount: float
    calc_type: Optional[str] = "vtb"
    payer_inn: Optional[str] = None
    payee_inn: Optional[str] = None
    payer_name: Optional[str] = None
    payee_name: Optional[str] = None
    purpose: Optional[str] = None
    category_code: Optional[str] = None
    income_expense_id: Optional[str] = None
    ignore_flag: Optional[str] = "Нет"


class LinkedPaymentInfo(BaseModel):
    """Краткая информация о привязанном платеже."""
    id: Union[str, UUID]
    doc_num: Optional[str] = None
    transaction_date: Optional[date] = None
    amount: Optional[float] = None

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value


class TreasuryTransactionResponse(TreasuryTransactionBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    allocations: List[TreasuryAllocationResponse] = []
    allocated_amount: Optional[float] = None
    remainder: Optional[float] = None
    auto_rule_id: Optional[str] = None
    auto_filled: bool = False  # True if auto_rule_id is set
    linked_transaction_id: Optional[Union[str, UUID]] = None
    linked_payments: List[LinkedPaymentInfo] = []  # платежи, привязанные к этому

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id", "linked_transaction_id")
    def serialize_id_fields(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value


class TreasuryTransactionCreate(TreasuryTransactionBase):
    """Schema for creating a treasury transaction manually."""
    pass


class TreasuryTransactionUpdate(BaseModel):
    calc_type: Optional[str] = None
    category_code: Optional[str] = None
    ignore_flag: Optional[str] = None
    income_expense_id: Optional[str] = None
    linked_transaction_id: Optional[str] = None
