"""
Pydantic schemas for StageProductSubtask model.
"""
from typing import Optional, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer, field_validator


class StageProductSubtaskBase(BaseModel):
    assignment_id: Union[str, UUID]
    title: str
    due_date: Optional[date] = None
    status: Optional[str] = "not_started"

    @field_validator("assignment_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return value
        return value


class StageProductSubtaskCreate(StageProductSubtaskBase):
    pass


class StageProductSubtaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class StageProductSubtaskResponse(StageProductSubtaskBase):
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

    @field_serializer("due_date")
    def serialize_date(self, value):
        if isinstance(value, date):
            return value.isoformat()
        return value
