"""
Pydantic schemas for Treasury Auto Rules
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer


class TreasuryAutoRuleBase(BaseModel):
    name: str
    match_text: str
    match_type: str = "contains"  # contains, starts_with, ends_with, regex
    action_type: str  # category, ignore, create_dds
    category_code: Optional[str] = None
    create_dds: bool = False
    is_active: bool = True
    priority: int = 100


class TreasuryAutoRuleCreate(TreasuryAutoRuleBase):
    pass


class TreasuryAutoRuleUpdate(BaseModel):
    name: Optional[str] = None
    match_text: Optional[str] = None
    match_type: Optional[str] = None
    action_type: Optional[str] = None
    category_code: Optional[str] = None
    create_dds: Optional[bool] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class TreasuryAutoRuleResponse(TreasuryAutoRuleBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
