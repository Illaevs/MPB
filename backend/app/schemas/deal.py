"""
Pydantic schemas for Deal model
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID

class DealBase(BaseModel):
    title: str
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    customer_id: Optional[Union[str, UUID]] = None
    our_company_id: Optional[Union[str, UUID]] = None
    general_contractor_id: Optional[Union[str, UUID]] = None
    penalty_config: Optional[dict] = None
    s3_prefix_tz: Optional[str] = None
    s3_prefix_docs: Optional[str] = None
    status: Optional[str] = "active"
    total_contract_value: Optional[float] = 0.0
    total_paid: Optional[float] = 0.0
    vat_rate: Optional[float] = 20.0
    vat_included: Optional[bool] = True

    @field_validator('customer_id', 'our_company_id', 'general_contractor_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

class DealCreate(DealBase):
    title: str  # Обязательное поле

class DealUpdate(BaseModel):
    title: Optional[str] = None
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    customer_id: Optional[Union[str, UUID]] = None
    our_company_id: Optional[Union[str, UUID]] = None
    general_contractor_id: Optional[Union[str, UUID]] = None
    penalty_config: Optional[dict] = None
    s3_prefix_tz: Optional[str] = None
    s3_prefix_docs: Optional[str] = None
    status: Optional[str] = None
    total_contract_value: Optional[float] = None
    total_paid: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_included: Optional[bool] = None

    class Config:
        extra = "forbid"

    @field_validator('customer_id', 'our_company_id', 'general_contractor_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

class DealResponse(DealBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('id')
    def serialize_id(self, value):
        """Convert UUID to string for JSON serialization"""
        if isinstance(value, UUID):
            return str(value)
        return value


class DealVatUpdate(BaseModel):
    vat_rate: Optional[float] = None
    vat_included: Optional[bool] = None

    class Config:
        extra = "forbid"


class DealGipsUpdate(BaseModel):
    user_ids: list[str] = []

    class Config:
        extra = "forbid"
