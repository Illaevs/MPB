"""
Pydantic schemas for SubcontractorProduct model
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID


class SubcontractorProductBase(BaseModel):
    subcontractor_card_id: Union[str, UUID]
    contract_id: Optional[Union[str, UUID]] = None
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
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = "planned"
    notes: Optional[str] = None
    custom_properties: Optional[dict] = {}

    @field_validator('subcontractor_card_id', 'contract_id', 'product_id', 'stage_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return v
        return v


class SubcontractorProductCreate(SubcontractorProductBase):
    subcontractor_card_id: Union[str, UUID]
    product_id: Union[str, UUID]
    quantity: float
    unit_price: float


class SubcontractorProductUpdate(BaseModel):
    custom_name: Optional[str] = None
    custom_price: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    currency: Optional[str] = None
    contract_id: Optional[Union[str, UUID]] = None
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    custom_properties: Optional[dict] = None

    @field_validator('stage_id', 'contract_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return v
        return v


class SubcontractorProductResponse(SubcontractorProductBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('id')
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
