from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class QualityAlertCreate(BaseModel):
    deal_id: UUID
    alert_type: str
    severity: str = "info"
    message: str


class QualityAlertResponse(QualityAlertCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
