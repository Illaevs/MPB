from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OverheadAllocationResponse(BaseModel):
    id: UUID
    deal_id: UUID
    period: str
    amount: float
    calc_version: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
