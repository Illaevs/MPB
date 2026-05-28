"""Pydantic-схемы корпоративной ленты новостей."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---- Attachments ----------------------------------------------------------

class FeedAttachment(BaseModel):
    url: str
    name: Optional[str] = None
    # kind: "image" — inline-галерея, "file" — список «скрепок».
    # У старых постов поле отсутствует → дефолт "image" (исторический
    # тип). Это обеспечивает обратную совместимость с уже сохранёнными
    # attachments в БД до появления произвольных файлов.
    kind: Optional[str] = "image"
    size: Optional[int] = None


# ---- Author brief ---------------------------------------------------------

class FeedAuthor(BaseModel):
    id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None


# ---- Polls ----------------------------------------------------------------

class FeedPollInput(BaseModel):
    """Конфиг опроса при создании поста. `options` — тексты вариантов,
    id бэкенд генерирует сам."""
    multi: bool = False
    anonymous: bool = False
    options: List[str] = []

    @field_validator("options")
    @classmethod
    def _clean_options(cls, v):
        out = []
        for o in (v or []):
            s = str(o or "").strip()
            if s:
                out.append(s[:300])
        return out


class FeedPollOption(BaseModel):
    id: str
    text: str
    votes: int = 0
    voted: bool = False                 # текущий пользователь выбрал этот вариант
    voters: List[FeedAuthor] = []       # кто проголосовал (пусто, если anonymous)


class FeedPoll(BaseModel):
    multi: bool = False
    anonymous: bool = False
    options: List[FeedPollOption] = []
    total_votes: int = 0                # уникальных проголосовавших
    my_voted: bool = False              # текущий пользователь уже голосовал


# ---- Reactions ------------------------------------------------------------

class FeedReactionGroup(BaseModel):
    emoji: str
    count: int = 0
    mine: bool = False                  # текущий пользователь поставил этот эмодзи


# ---- Posts ----------------------------------------------------------------

class FeedPostCreate(BaseModel):
    body: str = Field(default="", max_length=20000)
    post_type: str = Field(default="news")
    is_pinned: bool = False
    attachments: List[FeedAttachment] = []
    poll: Optional[FeedPollInput] = None

    @field_validator("post_type")
    @classmethod
    def _type_ok(cls, v):
        return v if v in ("news", "post") else "news"


class FeedPostPatch(BaseModel):
    body: Optional[str] = Field(default=None, max_length=20000)
    post_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    attachments: Optional[List[FeedAttachment]] = None

    @field_validator("post_type")
    @classmethod
    def _type_ok(cls, v):
        if v is None:
            return v
        return v if v in ("news", "post") else "news"


class FeedPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author: Optional[FeedAuthor] = None
    body: str
    post_type: str = "news"
    is_pinned: bool = False
    attachments: List[FeedAttachment] = []
    poll: Optional[FeedPoll] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Агрегаты
    reactions: List[FeedReactionGroup] = []
    comments_count: int = 0
    views_count: int = 0
    can_edit: bool = False


# ---- Comments -------------------------------------------------------------

class FeedCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)


class FeedCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    author: Optional[FeedAuthor] = None
    body: str
    created_at: Optional[datetime] = None
    can_delete: bool = False


# ---- Actions --------------------------------------------------------------

class FeedReactRequest(BaseModel):
    """Переключить (toggle) эмодзи-реакцию на посте."""
    emoji: str = Field(..., min_length=1, max_length=16)


class FeedVoteRequest(BaseModel):
    """Проголосовать в опросе. Для single-choice опроса учитывается
    первый из `option_ids`; для multi — весь набор."""
    option_ids: List[str] = []
