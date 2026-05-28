"""
Pydantic schemas for StageProductAssignment model.
"""
from typing import Optional, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer, field_validator


class StageProductAssignmentBase(BaseModel):
    deal_id: Union[str, UUID]
    stage_id: Union[str, UUID]
    product_id: Union[str, UUID]
    subcontractor_card_id: Union[str, UUID]
    subcontractor_product_id: Optional[Union[str, UUID]] = None
    contract_id: Optional[Union[str, UUID]] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    contract_due_date: Optional[date] = None
    status: Optional[str] = "not_started"

    @field_validator(
        "deal_id",
        "stage_id",
        "product_id",
        "subcontractor_card_id",
        "subcontractor_product_id",
        "contract_id",
        mode="before",
    )
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return value
        return value


class StageProductAssignmentCreate(StageProductAssignmentBase):
    pass


class StageProductAssignmentUpdate(BaseModel):
    subcontractor_product_id: Optional[Union[str, UUID]] = None
    contract_id: Optional[Union[str, UUID]] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    contract_due_date: Optional[date] = None
    status: Optional[str] = None

    @field_validator("subcontractor_product_id", "contract_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return value
        return value


class StageProductAssignmentResponse(StageProductAssignmentBase):
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

    @field_serializer("start_date", "due_date", "contract_due_date")
    def serialize_date(self, value):
        if isinstance(value, date):
            return value.isoformat()
        return value
