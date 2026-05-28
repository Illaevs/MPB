"""
Pydantic schemas for messenger conversations.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_serializer


def serialize_utc_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None

    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ChatMessageReferenceResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    body: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    is_deleted: bool = False
    created_at: Optional[datetime] = None

    @field_serializer("created_at")
    def serialize_created_at(self, value: Optional[datetime]) -> Optional[str]:
        return serialize_utc_datetime(value)

    class Config:
        from_attributes = True


class ChatConversationMemberResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: Optional[str] = None
    role: str = "member"
    joined_at: Optional[datetime] = None

    @field_serializer("joined_at")
    def serialize_joined_at(self, value: Optional[datetime]) -> Optional[str]:
        return serialize_utc_datetime(value)

    class Config:
        from_attributes = True


class ChatConversationResponse(BaseModel):
    id: str
    type: str
    title: str
    description: Optional[str] = None
    member_count: int = 0
    can_manage_members: bool = False
    members: List[ChatConversationMemberResponse] = Field(default_factory=list)
    last_message: Optional[ChatMessageReferenceResponse] = None
    pinned_message: Optional[ChatMessageReferenceResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("created_at", "updated_at")
    def serialize_timestamps(self, value: Optional[datetime]) -> Optional[str]:
        return serialize_utc_datetime(value)

    class Config:
        from_attributes = True


class ChatConversationCreate(BaseModel):
    type: Literal["group", "channel"]
    title: str
    description: Optional[str] = None
    member_ids: List[str] = Field(default_factory=list)


class ChatConversationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ChatConversationDirectCreate(BaseModel):
    user_id: str


class ChatConversationMemberAdd(BaseModel):
    user_ids: List[str] = Field(default_factory=list)
