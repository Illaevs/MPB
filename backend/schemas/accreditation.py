"""
Schemas for CompanyAccreditation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_serializer


class AccreditationBase(BaseModel):
    company_id: str
    direction_id: str
    status: Optional[str] = None
    comment: Optional[str] = None


class AccreditationCreate(AccreditationBase):
    company_id: str
    direction_id: str


class AccreditationUpdate(BaseModel):
    status: Optional[str] = None
    comment: Optional[str] = None


class AccreditationRequest(BaseModel):
    company_id: str
    direction_ids: List[str]


class AccreditationResponse(BaseModel):
    id: str
    company_id: str
    direction_id: str
    status: str
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id", "company_id", "direction_id")
    def serialize_id(self, value):
        return str(value) if value is not None else None
