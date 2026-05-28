"""
Pydantic schemas for SubcontractorCard model
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID


class SubcontractorBase(BaseModel):
    title: str
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    company_id: Optional[Union[str, UUID]] = None
    customer_id: Optional[Union[str, UUID]] = None
    general_contractor_id: Optional[Union[str, UUID]] = None
    penalty_config: Optional[dict] = None
    s3_prefix_tz: Optional[str] = None
    s3_prefix_docs: Optional[str] = None
    status: Optional[str] = "active"
    total_contract_value: Optional[float] = 0.0
    total_paid: Optional[float] = 0.0
    vat_rate: Optional[float] = 20.0
    vat_included: Optional[bool] = True

    @field_validator('company_id', 'customer_id', 'general_contractor_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, UUID):
            return str(v)
        if isinstance(v, str):
            value = v.strip()
            if not value:
                return None
            try:
                return str(UUID(value))
            except ValueError:
                return None
        return v


class SubcontractorCreate(SubcontractorBase):
    title: str


class SubcontractorUpdate(BaseModel):
    title: Optional[str] = None
    obj_name: Optional[str] = None
    address: Optional[str] = None
    object_type: Optional[str] = None
    object_area: Optional[float] = None
    company_id: Optional[Union[str, UUID]] = None
    customer_id: Optional[Union[str, UUID]] = None
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
        extra = "ignore"

    @field_validator('company_id', 'customer_id', 'general_contractor_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, UUID):
            return str(v)
        if isinstance(v, str):
            value = v.strip()
            if not value:
                return None
            try:
                return str(UUID(value))
            except ValueError:
                return None
        return v


class SubcontractorResponse(SubcontractorBase):
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
