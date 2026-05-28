from typing import Optional, List
from datetime import date

from pydantic import BaseModel


class PaymentHistoryItem(BaseModel):
    transaction_id: str
    transaction_date: Optional[date] = None
    amount: float
    doc_num: Optional[str] = None
    allocation_id: Optional[str] = None
    category_code: Optional[str] = None


class IncomeExpenseEntryBase(BaseModel):
    direction: str
    amount: float
    plan_date: date
    actual_date: Optional[date] = None
    payer_id: Optional[str] = None
    payee_id: Optional[str] = None
    deal_id: Optional[str] = None
    contract_id: Optional[str] = None
    stage_id: Optional[str] = None
    category_code: Optional[str] = None


class IncomeExpenseEntryCreate(IncomeExpenseEntryBase):
    pass


class IncomeExpenseEntryUpdate(BaseModel):
    direction: Optional[str] = None
    amount: Optional[float] = None
    plan_date: Optional[date] = None
    actual_date: Optional[date] = None
    payer_id: Optional[str] = None
    payee_id: Optional[str] = None
    deal_id: Optional[str] = None
    contract_id: Optional[str] = None
    category_code: Optional[str] = None


class IncomeExpenseEntryResponse(IncomeExpenseEntryBase):
    id: str
    payer_name: Optional[str] = None
    payee_name: Optional[str] = None
    deal_title: Optional[str] = None
    contract_number: Optional[str] = None
    payment_status: str
    paid_amount: float
    payments_history: List[PaymentHistoryItem]
    warning: Optional[str] = None
