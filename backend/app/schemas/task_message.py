"""
Pydantic schemas for TaskMessage model.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TaskMessageCreate(BaseModel):
    body: Optional[str] = None
    mentions: Optional[List[str]] = []


class TaskMessageUpdate(BaseModel):
    body: Optional[str] = None


class TaskMessageResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    user_name: Optional[str] = None
    body: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    mentions: List[str] = []
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

