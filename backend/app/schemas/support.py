"""
Pydantic schemas for the support ticket system.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

CATEGORIES = ("bug", "improvement", "access", "question", "other")
STATUSES = ("new", "in_progress", "waiting_user", "resolved", "closed", "rejected")


class SupportTicketCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    category: Optional[str] = "other"
    model_config = ConfigDict(extra="forbid")


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    assignee_id: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class SupportMessageResponse(BaseModel):
    id: str
    ticket_id: str
    user_id: str
    user_name: Optional[str] = None
    body: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    is_internal: bool = False
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class SupportTicketResponse(BaseModel):
    id: str
    number: Optional[int] = None
    subject: str
    description: Optional[str] = None
    category: str = "other"
    status: str = "new"
    created_by_id: str
    created_by_name: Optional[str] = None
    created_by_avatar: Optional[str] = None
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    linked_task_id: Optional[str] = None
    linked_task_number: Optional[int] = None
    attachments: List[Dict[str, Any]] = []
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    last_message_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class SupportTicketDetail(SupportTicketResponse):
    messages: List[SupportMessageResponse] = []


class SupportMessageUpdate(BaseModel):
    body: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class CreateTaskFromTicket(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    priority: Optional[str] = "normal"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    model_config = ConfigDict(extra="forbid")
