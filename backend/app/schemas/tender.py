"""
Schemas for Tender.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_serializer


class TenderBase(BaseModel):
    deal_product_id: str
    status: Optional[str] = None
    winner_company_id: Optional[str] = None


class TenderCreate(TenderBase):
    deal_product_id: str
    submission_deadline: Optional[datetime] = None


class TenderUpdate(BaseModel):
    status: Optional[str] = None
    winner_company_id: Optional[str] = None
    submission_deadline: Optional[datetime] = None


class TenderResponse(BaseModel):
    id: str
    deal_product_id: str
    deal_id: str
    product_id: str
    direction_id: Optional[str] = None
    status: str
    winner_company_id: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id", "deal_product_id", "deal_id", "product_id", "direction_id", "winner_company_id")
    def serialize_id(self, value):
        return str(value) if value is not None else None
