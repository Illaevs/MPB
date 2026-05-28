"""
Pydantic schemas for RolePermission model.
"""
from typing import Optional, Union
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer


class RolePermissionBase(BaseModel):
    role_id: Optional[Union[str, UUID]] = None
    section: str
    read_all: Optional[bool] = False
    read_assigned: Optional[bool] = False
    edit_all: Optional[bool] = False
    edit_assigned: Optional[bool] = False


class RolePermissionUpdate(BaseModel):
    read_all: Optional[bool] = None
    read_assigned: Optional[bool] = None
    edit_all: Optional[bool] = None
    edit_assigned: Optional[bool] = None


class RolePermissionSet(BaseModel):
    section: str
    read_all: Optional[bool] = False
    read_assigned: Optional[bool] = False
    edit_all: Optional[bool] = False
    edit_assigned: Optional[bool] = False


class RolePermissionResponse(RolePermissionBase):
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
