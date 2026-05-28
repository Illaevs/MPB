"""
Pydantic schemas for FinancialPlan model
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer
from datetime import datetime, date
from uuid import UUID

class FinancialPlanBase(BaseModel):
    deal_id: str
    direction: str  # "income" or "expense"
    amount_plan: float
    date_plan_start: Optional[date] = None
    date_plan_end: Optional[date] = None
    description: Optional[str] = None
    contractor_id: Optional[str] = None
    subcontractor_contract_id: Optional[str] = None
    payment_status: Optional[str] = "unpaid"
    stage_id: Optional[str] = None

class FinancialPlanCreate(FinancialPlanBase):
    deal_id: str  # Required field
    direction: str  # Required field
    amount_plan: float  # Required field

class FinancialPlanUpdate(FinancialPlanBase):
    pass

class FinancialPlanResponse(FinancialPlanBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('id')
    def serialize_id(self, value):
        """Convert UUID to string for JSON serialization"""
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_serializer('date_plan_start', 'date_plan_end')
    def serialize_date(self, value):
        """Convert date to ISO format string"""
        if isinstance(value, date):
            return value.isoformat()
        return value
