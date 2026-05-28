"""
Task subtask (a.k.a. checklist item) model.

Полноценные подзадачи: текст + чекбокс выполнения + опциональный
ответственный и дедлайн + порядок сортировки. Показываются под
описанием задачи в модалке.

Отделены в собственную таблицу (не JSON в Task), потому что:
- нужны ссылки на user_id с FK-целостностью;
- сортировка/drag-reorder требует независимого update порядка;
- легко расширить (комменты, события, статусы) без миграции схемы.
"""
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TaskSubtask(Base):
    __tablename__ = "task_subtasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)

    title = Column(Text, nullable=False)
    is_done = Column(Boolean, nullable=False, default=False)
    # «Огонёк»: пользовательский флаг важности пункта чек-листа. В UI
    # отображается тем же `fas fa-fire` (красный), что и urgent-приоритет
    # задачи — чтобы юзер сразу узнавал значок.
    is_urgent = Column(Boolean, nullable=False, default=False)

    # Опциональный ответственный — отдельный от ответственных задачи.
    # Может быть None — пункт без конкретного исполнителя.
    assigned_to_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    # Опциональный дедлайн пункта чек-листа.
    due_date = Column(Date, nullable=True)
    # Время дедлайна 'HH:MM' — повторяет шаблон Task.due_time.
    due_time = Column(String(5), nullable=True)

    # Порядок отображения внутри задачи. На вставке — MAX(sort_order)+1.
    # На drag-reorder фронт шлёт полный список id-шников в нужном
    # порядке, бэк проставляет sort_order через индекс. Без unique —
    # допускаем одинаковые значения при гонке, ребалансируем при
    # следующем reorder.
    sort_order = Column(Integer, nullable=False, default=0)

    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task")
    assignee = relationship("User", foreign_keys=[assigned_to_user_id])
    creator = relationship("User", foreign_keys=[created_by_user_id])
