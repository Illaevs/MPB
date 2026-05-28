"""
Per-user "last read" marker for a task's chat thread.

Used to compute unread-message counts for the task list/kanban
indicators. Entry semantics:
- (user_id, task_id) — composite PK; one row per user/task pair.
- `last_read_at` — server-time when the user last opened the task
  (and therefore is considered to have seen all messages up to that
  point). Updated via `mark_task_read` endpoint when modal opens.
- Unread count for user U on task T = count(TaskMessage where
  task_id=T, user_id != U, is_deleted=false, created_at > last_read_at).
  If row is absent → all non-own messages count as unread.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class TaskRead(Base):
    __tablename__ = "task_reads"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), primary_key=True)
    last_read_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
