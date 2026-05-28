from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class InflationIndexBase(BaseModel):
    period: str
    value: float = 1.0
    note: Optional[str] = None


class InflationIndexCreate(InflationIndexBase):
    pass


class InflationIndexUpdate(BaseModel):
    period: Optional[str] = None
    value: Optional[float] = None
    note: Optional[str] = None


class InflationIndexResponse(InflationIndexBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
