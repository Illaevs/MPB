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

    # Per-user state (Stage 1 implicit DM).
    # unread_count — число сообщений с created_at > last_read_at.
    # is_archived  — true, если ТЕКУЩИЙ юзер архивировал чат у себя.
    # muted_until  — None или будущий момент; вычисляется на запросе.
    # last_read_at — для синхронизации с другими клиентами этого юзера.
    unread_count: int = 0
    is_archived: bool = False
    muted_until: Optional[datetime] = None
    last_read_at: Optional[datetime] = None

    @field_serializer("created_at", "updated_at", "muted_until", "last_read_at")
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


class ChatConversationStateUpdate(BaseModel):
    """PATCH /conversations/{id}/me — управление per-user state.

    Поля опциональны: можно прислать только то, что меняем. `muted_forever`
    True переводит chat в «навсегда заглушено» (сохраняется как далёкая
    дата в muted_until).
    """

    is_archived: Optional[bool] = None
    muted_until: Optional[datetime] = None
    muted_forever: Optional[bool] = None


class SearchableUserResponse(BaseModel):
    """GET /chat/users/searchable — список юзеров для «написать коллеге».

    Отдаёт ВСЕХ активных юзеров (кроме самого вызывающего); пометка
    `has_dm` подсказывает фронту «уже есть чат» vs «новый».
    """

    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    has_dm: bool = False
    dm_conversation_id: Optional[str] = None

    class Config:
        from_attributes = True
