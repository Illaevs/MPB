from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PricingQuoteCreate(BaseModel):
    deal_id: UUID
    model_id: Optional[UUID] = None
    calc_date: Optional[date] = None
    margin: Optional[float] = None
    risk: Optional[float] = None


class PricingQuoteResponse(BaseModel):
    id: UUID
    deal_id: UUID
    model_id: Optional[UUID] = None
    calc_date: date
    base_cost: float
    overheads: float
    indexed_cost: float
    risk: float
    margin: float
    final_price: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
