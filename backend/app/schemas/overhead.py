from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OverheadBase(BaseModel):
    period: str
    amount: float = 0.0
    category: Optional[str] = None
    source: Optional[str] = "manual"


class OverheadCreate(OverheadBase):
    pass


class OverheadUpdate(BaseModel):
    period: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    source: Optional[str] = None


class OverheadResponse(OverheadBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
