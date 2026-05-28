"""
Pydantic schemas for Lead model.
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID


class LeadBase(BaseModel):
    title: str
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    customer_id: Optional[Union[str, UUID]] = None
    our_company_id: Optional[Union[str, UUID]] = None
    responsible_user_id: Optional[Union[str, UUID]] = None
    advance_percent: Optional[float] = 0.0
    vat_rate: Optional[float] = 20.0
    status: Optional[str] = "incoming"
    total_value: Optional[float] = 0.0
    deal_id: Optional[Union[str, UUID]] = None

    @field_validator("customer_id", "our_company_id", "deal_id", "responsible_user_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return None
        return value


class LeadCreate(LeadBase):
    title: str


class LeadUpdate(BaseModel):
    title: Optional[str] = None
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    customer_id: Optional[Union[str, UUID]] = None
    our_company_id: Optional[Union[str, UUID]] = None
    responsible_user_id: Optional[Union[str, UUID]] = None
    advance_percent: Optional[float] = None
    vat_rate: Optional[float] = None
    status: Optional[str] = None
    total_value: Optional[float] = None
    deal_id: Optional[Union[str, UUID]] = None

    class Config:
        extra = "ignore"

    @field_validator("customer_id", "our_company_id", "deal_id", "responsible_user_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return None
        return value


class LeadResponse(LeadBase):
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
