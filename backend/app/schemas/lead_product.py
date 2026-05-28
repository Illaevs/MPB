"""
Pydantic schemas for LeadProduct model.
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID


class LeadProductBase(BaseModel):
    lead_id: Union[str, UUID]
    product_id: Union[str, UUID]
    custom_name: Optional[str] = None
    custom_price: Optional[float] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: float
    discount_percent: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    tax_rate: Optional[float] = 0.0
    currency: Optional[str] = "RUB"
    total_price: Optional[float] = None
    discount_total: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    final_price: Optional[float] = None
    notes: Optional[str] = None
    custom_properties: Optional[dict] = {}

    @field_validator("lead_id", "product_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return value
        return value


class LeadProductCreate(LeadProductBase):
    lead_id: Union[str, UUID]
    product_id: Union[str, UUID]
    quantity: float
    unit_price: float


class LeadProductUpdate(BaseModel):
    custom_name: Optional[str] = None
    custom_price: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    custom_properties: Optional[dict] = None


class LeadProductResponse(LeadProductBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
