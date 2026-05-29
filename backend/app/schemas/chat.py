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

    # Per-user state (Stage 1 implicit DM + Phase B).
    # unread_count — число сообщений с created_at > last_read_at.
    # is_archived  — true, если ТЕКУЩИЙ юзер архивировал чат у себя.
    # muted_until  — None или будущий момент; вычисляется на запросе.
    # last_read_at — для синхронизации с другими клиентами этого юзера.
    # is_pinned    — закреплён ли чат сверху у меня (Phase B.1).
    # peer_last_read_at — Phase B.2: для DM-чатов last_read_at второго
    #                     участника. Фронт сравнивает с моими
    #                     message.created_at для ✓/✓✓.
    unread_count: int = 0
    is_archived: bool = False
    muted_until: Optional[datetime] = None
    last_read_at: Optional[datetime] = None
    is_pinned: bool = False
    peer_last_read_at: Optional[datetime] = None

    @field_serializer(
        "created_at", "updated_at", "muted_until", "last_read_at",
        "peer_last_read_at",
    )
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
    is_pinned: Optional[bool] = None


class MessageReactionAggregate(BaseModel):
    """Агрегат реакций по одной emoji-метке для одного сообщения.

    На фронт уходит уже сгруппированный набор: на сообщение → список
    MessageReactionAggregate (по одной на уникальный emoji), внутри —
    счётчик и список user_id (для определения «реагировал ли я»).
    """

    emoji: str
    count: int
    user_ids: List[str] = Field(default_factory=list)
    reacted_by_me: bool = False


class ReactionToggleRequest(BaseModel):
    """POST /chat/messages/{id}/reactions — body {emoji: '👍'}.

    Эндпоинт идемпотентно toggle'ит мою реакцию: если такой пары
    (message, me, emoji) ещё нет — создаёт; если есть — удаляет.
    Возвращает обновлённое сообщение целиком.
    """

    emoji: str = Field(..., min_length=1, max_length=32)


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


class TypingPresence(BaseModel):
    """Один юзер, печатающий в conversation прямо сейчас.

    `at` — timestamp последнего typing-сигнала, фронт использует для
    fade-out (если at > 5с назад — считаем «остановился»).
    """

    user_id: str
    user_name: Optional[str] = None
    at: datetime

    @field_serializer("at")
    def serialize_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value)


class MentionItem(BaseModel):
    """GET /chat/mention-search — единый формат для мiks результата.

    kind:
      'user' — id юзера, label = full_name|email
      'deal' — id сделки, label = title|obj_name
      'task' — id задачи, label = title
    """

    kind: Literal["user", "deal", "task"]
    id: str
    label: str
    sublabel: Optional[str] = None
    avatar_url: Optional[str] = None
    href: Optional[str] = None  # маршрут для перехода во фронте
