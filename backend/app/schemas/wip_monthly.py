from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WipMonthlyResponse(BaseModel):
    id: UUID
    deal_id: UUID
    stage_id: UUID
    period: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    is_forecast: bool
    calc_version: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
