from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AdvancePaymentBase(BaseModel):
    deal_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    amount_total: float = 0.0
    vat_rate: float = 20.0
    remaining_total: float = 0.0


class AdvancePaymentCreate(AdvancePaymentBase):
    pass


class AdvancePaymentUpdate(BaseModel):
    amount_total: Optional[float] = None
    remaining_total: Optional[float] = None
    vat_rate: Optional[float] = None


class AdvancePaymentResponse(AdvancePaymentBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
