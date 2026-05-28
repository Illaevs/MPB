"""
Penalty Rule schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PenaltyRuleBase(BaseModel):
    rule_type: str  # "rating" | "deadline"
    condition_min: float
    condition_max: float
    coefficient: float = 1.0
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PenaltyRuleCreate(PenaltyRuleBase):
    pass


class PenaltyRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    condition_min: Optional[float] = None
    condition_max: Optional[float] = None
    coefficient: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PenaltyRuleResponse(PenaltyRuleBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
