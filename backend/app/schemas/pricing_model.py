from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PricingModelBase(BaseModel):
    name: str
    base_margin: float = 0.0
    risk_reserve: float = 0.0
    inflation_mode: str = "auto"


class PricingModelCreate(PricingModelBase):
    pass


class PricingModelUpdate(BaseModel):
    name: Optional[str] = None
    base_margin: Optional[float] = None
    risk_reserve: Optional[float] = None
    inflation_mode: Optional[str] = None


class PricingModelResponse(PricingModelBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
