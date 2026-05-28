"""
Pydantic schemas for DealProduct model
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_serializer, field_validator
from datetime import datetime
from uuid import UUID
from app.schemas.product import ProductResponse

class DealProductBase(BaseModel):
    deal_id: Union[str, UUID]
    product_id: Union[str, UUID]
    custom_name: Optional[str] = None
    custom_price: Optional[float] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: float
    discount_percent: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    tax_rate: Optional[float] = 0.0
    tax_included: Optional[bool] = False
    currency: Optional[str] = "RUB"
    total_price: Optional[float] = None
    discount_total: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    final_price: Optional[float] = None
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = "planned"
    notes: Optional[str] = None
    custom_properties: Optional[dict] = {}

    @field_validator('deal_id', 'product_id', 'stage_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return v  # Return as string if not a valid UUID
        return v

class DealProductCreate(DealProductBase):
    deal_id: Union[str, UUID]  # Required field
    product_id: Union[str, UUID]  # Required field
    quantity: float  # Required field
    unit_price: float  # Required field

class DealProductUpdate(BaseModel):
    custom_name: Optional[str] = None
    custom_price: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_included: Optional[bool] = None
    currency: Optional[str] = None
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    custom_properties: Optional[dict] = None

    @field_validator('stage_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return v  # Return as string if not a valid UUID
        return v

class DealProductInvoiceLinkResponse(BaseModel):
    document_id: str
    number_in_contract: Optional[int] = None
    amount: Optional[float] = None


class DealProductResponse(DealProductBase):
    id: Union[str, UUID]
    product: Optional[ProductResponse] = None
    invoice_links: List[DealProductInvoiceLinkResponse] = Field(default_factory=list)
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
