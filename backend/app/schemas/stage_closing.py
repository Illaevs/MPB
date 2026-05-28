from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StageClosingBase(BaseModel):
    stage_id: UUID
    deal_id: UUID
    contract_id: Optional[UUID] = None
    closing_date: date
    base_amount: float


class StageClosingCreate(StageClosingBase):
    pass


class StageClosingResponse(StageClosingBase):
    id: UUID
    vat_rate: float
    vat_amount: float
    total_amount: float
    advance_covered_base: float
    advance_covered_vat: float
    remaining_base: float
    remaining_vat: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
