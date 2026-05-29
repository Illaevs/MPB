"""
Pydantic schemas for TaskMessage model.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


# Phase D.3 — расширенный формат mentions.
# Старый: список строк-user_id.
# Новый: список объектов {kind, id, label, href} для рендера ссылок
# на сущности (user/deal/task/contract/lead).
MentionItem = Union[str, Dict[str, Any]]


class TaskMessageCreate(BaseModel):
    body: Optional[str] = None
    mentions: Optional[List[MentionItem]] = []


class TaskMessageUpdate(BaseModel):
    body: Optional[str] = None


class TaskMessageResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    user_name: Optional[str] = None
    body: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    mentions: List[MentionItem] = []
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

