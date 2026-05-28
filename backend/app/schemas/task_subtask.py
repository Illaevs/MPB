"""
Pydantic schemas for TaskSubtask model — чек-лист внутри задачи.
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskSubtaskCreate(BaseModel):
    title: str
    assigned_to_user_id: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None  # 'HH:MM'
    is_urgent: Optional[bool] = False
    # sort_order не принимаем от клиента на create — бэк ставит сам как
    # MAX(sort_order)+1, чтобы новый пункт всегда оказывался в конце.


class TaskSubtaskUpdate(BaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None
    assigned_to_user_id: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    is_urgent: Optional[bool] = None


class TaskSubtaskReorder(BaseModel):
    # Полный список id-шников в нужном порядке. Бэк проставляет
    # sort_order = индекс. Проще и безопаснее (по дрейфу), чем
    # партиальный «двигать вверх/вниз».
    ids: List[str]


class TaskSubtaskResponse(BaseModel):
    id: str
    task_id: str
    title: str
    is_done: bool
    is_urgent: bool = False
    assigned_to_user_id: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    sort_order: int
    created_by_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    done_at: Optional[datetime] = None

    class Config:
        from_attributes = True
