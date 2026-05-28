"""
Pydantic schemas for Task model
"""
from typing import Any, Dict, Optional, Union, List
from urllib.parse import quote
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime, date
from uuid import UUID

from app.schemas.user import _resolve_avatar_filename


def _normalize_task_attachment(item: Any) -> Optional[Dict[str, Any]]:
    if isinstance(item, str):
        path = item.strip()
        if not path:
            return None
        name = path.replace("\\", "/").rsplit("/", 1)[-1] or "Файл"
        return {
            "name": name,
            "path": path,
            "size": None,
            "content_type": None,
            "download_url": f"/api/v1/storage/download?path={quote(path, safe='')}",
        }

    if isinstance(item, dict):
        normalized = dict(item)
        path = str(normalized.get("path") or "").strip()
        name = str(normalized.get("name") or "").strip()
        if not name:
            name = path.replace("\\", "/").rsplit("/", 1)[-1] if path else "Файл"
        normalized["name"] = name or "Файл"
        normalized["path"] = path or None
        if path:
            normalized["download_url"] = f"/api/v1/storage/download?path={quote(path, safe='')}"
        else:
            normalized.pop("download_url", None)
        return normalized

    return None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    deal_id: Optional[Union[str, UUID]] = None
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = "new"
    priority: Optional[str] = "normal"
    assigned_to_id: Optional[Union[str, UUID]] = None
    created_by_id: Optional[Union[str, UUID]] = None
    assigned_to_user_id: Optional[Union[str, UUID]] = None
    created_by_user_id: Optional[Union[str, UUID]] = None
    payer_id: Optional[Union[str, UUID]] = None
    payee_id: Optional[Union[str, UUID]] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = 0.0
    actual_hours: Optional[float] = 0.0
    budget: Optional[float] = None
    category_code: Optional[str] = None
    work_category: Optional[str] = None
    tags: Optional[List[str]] = []
    attachments: Optional[List[Dict[str, Any]]] = []
    notify_assigned: Optional[bool] = True
    notify_overdue: Optional[bool] = True

    @field_validator('deal_id', 'stage_id', 'assigned_to_id', 'created_by_id', 'assigned_to_user_id', 'created_by_user_id', 'payer_id', 'payee_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

    @field_validator('attachments', mode='before')
    @classmethod
    def normalize_attachments(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        normalized_items: List[Dict[str, Any]] = []
        for item in value:
            normalized = _normalize_task_attachment(item)
            if normalized:
                normalized_items.append(normalized)
        return normalized_items

class TaskCreate(TaskBase):
    title: str
    deal_id: Optional[Union[str, UUID]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage_id: Optional[Union[str, UUID]] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[Union[str, UUID]] = None
    assigned_to_user_id: Optional[Union[str, UUID]] = None
    created_by_user_id: Optional[Union[str, UUID]] = None
    payer_id: Optional[Union[str, UUID]] = None
    payee_id: Optional[Union[str, UUID]] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    budget: Optional[float] = None
    category_code: Optional[str] = None
    work_category: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    notify_assigned: Optional[bool] = None
    notify_overdue: Optional[bool] = None
    executor_rating: Optional[int] = None

    class Config:
        extra = "ignore"

    @field_validator('stage_id', 'assigned_to_id', 'assigned_to_user_id', 'created_by_user_id', 'payer_id', 'payee_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        if isinstance(v, str) and v:
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

    @field_validator('attachments', mode='before')
    @classmethod
    def normalize_attachments(cls, value):
        if value is None:
            return None
        if not isinstance(value, list):
            return []
        normalized_items: List[Dict[str, Any]] = []
        for item in value:
            normalized = _normalize_task_attachment(item)
            if normalized:
                normalized_items.append(normalized)
        return normalized_items

class TaskResponse(TaskBase):
    id: Union[str, UUID]
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('id')
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    def serialize_optional_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value

class TaskWithRelations(TaskResponse):
    deal_title: Optional[str] = None
    stage_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_by_name: Optional[str] = None
    assigned_to_user_name: Optional[str] = None
    assigned_to_user_avatar_url: Optional[str] = None
    created_by_user_name: Optional[str] = None
    created_by_user_avatar_url: Optional[str] = None
    payer_name: Optional[str] = None
    payee_name: Optional[str] = None
    source_auction_id: Optional[str] = None
    executor_rating: Optional[int] = None
    # Penalty/bonus fields
    final_budget: Optional[float] = None
    rating_coefficient: Optional[float] = None
    deadline_coefficient: Optional[float] = None
    penalty_amount: Optional[float] = None
    matrix_quadrant: Optional[str] = None
    matrix_sort_order: Optional[int] = None
    matrix_manual: Optional[bool] = False

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('assigned_to_user_avatar_url')
    def serialize_assigned_to_user_avatar_url(self, value):
        filename = _resolve_avatar_filename(self.assigned_to_user_id, value)
        if not filename or not self.assigned_to_user_id:
            return None
        return f"/api/v1/users/avatar-user/{self.serialize_optional_id(self.assigned_to_user_id)}"

    @field_serializer('created_by_user_avatar_url')
    def serialize_created_by_user_avatar_url(self, value):
        filename = _resolve_avatar_filename(self.created_by_user_id, value)
        if not filename or not self.created_by_user_id:
            return None
        return f"/api/v1/users/avatar-user/{self.serialize_optional_id(self.created_by_user_id)}"
