"""
Pydantic schemas for SubcontractorStage model
"""
from typing import Optional, Union, List
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime, date
from uuid import UUID


class SubcontractorStageBase(BaseModel):
    name: str
    description: Optional[str] = None
    stage_type: Optional[str] = "stage"
    term_type: Optional[str] = "work_days"
    date_start: date
    duration: int
    date_end: Optional[date] = None
    close_date: Optional[date] = None
    resources: Optional[List[dict]] = []
    planned_cost: Optional[float] = 0.0
    actual_cost: Optional[float] = 0.0
    status: Optional[str] = "planned"
    parent_id: Optional[UUID] = None
    subcontractor_card_id: Union[str, UUID]
    contract_id: Optional[Union[str, UUID]] = None
    subcontractor_id: Optional[UUID] = None

    @field_validator('subcontractor_card_id', 'contract_id', 'parent_id', 'subcontractor_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str):
            if v.strip() == '':
                return None
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

    @field_validator('date_start', 'date_end', 'close_date', mode='before')
    @classmethod
    def validate_date_fields(cls, v):
        if isinstance(v, str):
            if v.strip() == '':
                return None
            try:
                return date.fromisoformat(v)
            except ValueError:
                return None
        return v


class SubcontractorStageCreate(SubcontractorStageBase):
    pass


class SubcontractorStageUpdate(SubcontractorStageBase):
    pass


class SubcontractorStageResponse(SubcontractorStageBase):
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

    @field_serializer('date_start', 'date_end', 'close_date')
    def serialize_date(self, value):
        if isinstance(value, date):
            return value.isoformat()
        return value
