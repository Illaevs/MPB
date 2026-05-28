"""
Schemas for TenderOffer.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, field_serializer


class TenderOfferBase(BaseModel):
    tender_id: str
    company_id: str
    status: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_deadline: Optional[date] = None
    comment: Optional[str] = None


class TenderOfferCreate(TenderOfferBase):
    tender_id: str
    company_id: str


class TenderOfferUpdate(BaseModel):
    status: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_deadline: Optional[date] = None
    comment: Optional[str] = None


class TenderOfferResponse(BaseModel):
    id: str
    tender_id: str
    company_id: str
    status: str
    proposed_amount: Optional[float] = None
    proposed_deadline: Optional[date] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id", "tender_id", "company_id")
    def serialize_id(self, value):
        return str(value) if value is not None else None
