"""
Pydantic schemas for Contract model
"""
from typing import Optional, Union
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, field_serializer, field_validator


class ContractBase(BaseModel):
    contract_number: str
    contract_date: date
    status: Optional[str] = "approval"
    amount: Optional[float] = 0.0
    contract_type: str
    customer_id: Optional[Union[str, UUID]] = None
    executor_id: Optional[Union[str, UUID]] = None
    deal_id: Optional[Union[str, UUID]] = None
    subcontractor_card_id: Optional[Union[str, UUID]] = None

    @field_validator("customer_id", "executor_id", "deal_id", "subcontractor_card_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        if v == "":
            return None
        return v


class ContractCreate(ContractBase):
    contract_number: str
    contract_date: date
    contract_type: str


class ContractUpdate(BaseModel):
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    contract_type: Optional[str] = None
    customer_id: Optional[Union[str, UUID]] = None
    executor_id: Optional[Union[str, UUID]] = None
    deal_id: Optional[Union[str, UUID]] = None
    subcontractor_card_id: Optional[Union[str, UUID]] = None

    class Config:
        extra = "ignore"

    @field_validator("customer_id", "executor_id", "deal_id", "subcontractor_card_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        if v == "":
            return None
        return v


class ContractResponse(ContractBase):
    id: Union[str, UUID]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_serializer("contract_date")
    def serialize_date(self, value):
        if isinstance(value, date):
            return value.isoformat()
        return value
