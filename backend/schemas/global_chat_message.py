"""
Pydantic schemas for GlobalChatMessage model.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_serializer

from app.schemas.chat import ChatMessageReferenceResponse, serialize_utc_datetime


class GlobalChatMessageCreate(BaseModel):
    body: Optional[str] = None
    mentions: Optional[List[str]] = []


class GlobalChatMessageUpdate(BaseModel):
    body: Optional[str] = None


class GlobalChatMessageResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    conversation_id: Optional[str] = None
    body: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    is_deleted: bool = False
    is_pinned: bool = False
    pinned_at: Optional[datetime] = None
    pinned_by_user_id: Optional[str] = None
    reply_to_message: Optional[ChatMessageReferenceResponse] = None
    forwarded_from_message: Optional[ChatMessageReferenceResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @field_serializer("pinned_at", "created_at", "updated_at", "edited_at", "deleted_at")
    def serialize_timestamps(self, value: Optional[datetime]) -> Optional[str]:
        return serialize_utc_datetime(value)

    class Config:
        from_attributes = True
