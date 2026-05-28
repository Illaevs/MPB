"""
Pydantic schemas for OrgUnit (organisation structure tree).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class OrgUnitCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    kind: Optional[str] = None
    head_user_id: Optional[str] = None
    sort_order: Optional[int] = 0
    model_config = ConfigDict(extra="forbid")


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    kind: Optional[str] = None
    head_user_id: Optional[str] = None
    sort_order: Optional[int] = None
    model_config = ConfigDict(extra="forbid")


class OrgUnitMember(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True

    @field_serializer("id")
    def _ser_id(self, value):
        return str(value) if value is not None else None


class OrgUnitResponse(BaseModel):
    id: str
    parent_id: Optional[str] = None
    name: str
    kind: Optional[str] = None
    head_user_id: Optional[str] = None
    sort_order: int = 0
    depth: int = 0
    path: Optional[str] = None
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id", "parent_id", "head_user_id")
    def _ser_ids(self, value):
        return str(value) if value is not None else None


class OrgUnitTreeNode(OrgUnitResponse):
    children: List["OrgUnitTreeNode"] = []
    members: List[OrgUnitMember] = []


class OrgUnitAssign(BaseModel):
    user_id: str
    org_unit_id: Optional[str] = None
    model_config = ConfigDict(extra="forbid")
