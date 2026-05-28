"""
Pydantic schemas for Role model.
"""
from typing import Optional, Union
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class RoleResponse(RoleBase):
    id: Union[str, UUID]
    is_system: bool = False
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
