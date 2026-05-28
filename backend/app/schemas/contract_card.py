"""
Pydantic schemas for Contract card responses.
"""
from typing import List, Optional
from datetime import date

from pydantic import BaseModel

from app.schemas.contract import ContractResponse
from app.schemas.contract_document import ContractDocumentResponse
from app.schemas.income_expense import IncomeExpenseEntryResponse


class ContractPaymentSummary(BaseModel):
    total_amount: float
    paid_amount: float
    pending_amount: float


class ContractStageSummary(BaseModel):
    id: str
    name: str
    stage_type: str
    planned_cost: float
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    status: Optional[str] = None
    is_closed: Optional[bool] = None


class ContractCardResponse(BaseModel):
    contract: ContractResponse
    deal_title: Optional[str] = None
    subcontractor_title: Optional[str] = None
    documents: List[ContractDocumentResponse]
    payment_summary: ContractPaymentSummary
    payments: List[IncomeExpenseEntryResponse]
    stages: List[ContractStageSummary]
