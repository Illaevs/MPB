"""
Pydantic schemas for notifications.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer


def _count_cyrillic(text: str) -> int:
    return sum(1 for char in text if "А" <= char <= "я" or char in {"Ё", "ё"})


def _repair_mojibake(text: Optional[str]) -> Optional[str]:
    if not text:
        return text

    marker_count = sum(text.count(marker) for marker in ("Р", "С", "Ð", "Ñ", "вЂ"))
    if marker_count == 0:
        return text

    original_cyrillic = _count_cyrillic(text)
    candidates = []
    for encoding in ("cp1251", "latin1"):
        try:
            candidates.append(text.encode(encoding).decode("utf-8"))
        except UnicodeError:
            continue

    for candidate in candidates:
        if _count_cyrillic(candidate) > original_cyrillic:
            return candidate
    return text


class NotificationResponse(BaseModel):
    id: UUID
    user_id: str
    type: str
    priority: Optional[str] = None
    title: str
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action_url: Optional[str] = None
    rule_id: Optional[str] = None
    source_event_id: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    deliver_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id")
    def serialize_id(self, value):
        return str(value)

    @field_serializer("title")
    def serialize_title(self, value: str):
        return _repair_mojibake(value) or ""

    @field_serializer("message")
    def serialize_message(self, value: Optional[str]):
        return _repair_mojibake(value)
