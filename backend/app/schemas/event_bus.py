"""Pydantic-схемы для event-bus API."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventOutboxResponse(BaseModel):
    id: str
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    payload_version: int = 1
    status: str
    attempt_count: int = 0
    last_error: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class EventSubscriptionBase(BaseModel):
    name: str
    event_type_pattern: str
    delivery_method: str = "webhook"
    target_url: str
    hmac_secret: str
    is_active: bool = True
    description: Optional[str] = None


class EventSubscriptionCreate(EventSubscriptionBase):
    pass


class EventSubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    event_type_pattern: Optional[str] = None
    delivery_method: Optional[str] = None
    target_url: Optional[str] = None
    hmac_secret: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class EventSubscriptionResponse(EventSubscriptionBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
