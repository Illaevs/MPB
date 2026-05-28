"""
Task model - Задачи проекта
"""
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Date, Integer, Float, JSON, ForeignKey, Enum as SqlEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TaskPriority(str, PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, PyEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Sequential human-readable task number. Assigned on create as MAX(number)+1.
    # Unique across all tasks. Indexed for quick sort/lookup.
    number = Column(Integer, nullable=True, index=True, unique=True)

    # Основная информация
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Связи с проектом
    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=True)  # задача без проекта допустима
    stage_id = Column(String(36), ForeignKey("stages.id"), nullable=True)  # Опционально привязка к этапу

    # Статус и приоритет
    status = Column(SqlEnum("new", "in_progress", "pending", "completed", "cancelled", "deferred"), default="new")
    priority = Column(SqlEnum("low", "normal", "high", "urgent"), default="normal")

    # Ответственные
    assigned_to_id = Column(String(36), ForeignKey("companies.id"))  # legacy
    created_by_id = Column(String(36), ForeignKey("companies.id"))  # legacy
    assigned_to_user_id = Column(String(36), ForeignKey("users.id"))
    created_by_user_id = Column(String(36), ForeignKey("users.id"))
    payer_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    payee_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    income_expense_id = Column(String(36), ForeignKey("income_expense_entries.id"), nullable=True)

    # Сроки
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True, index=True)

    start_date = Column(Date)
    due_date = Column(Date)
    due_time = Column(String(5), nullable=True)  # 'HH:MM' (опционально, для встреч/заседаний)
    completed_at = Column(DateTime(timezone=True))

    # Дополнительная информация
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)

    # Теги и метки (JSON)
    tags = Column(JSON, default=list)

    # Файлы и комментарии (пути в S3)
    attachments = Column(JSON, default=list)  # Список путей к файлам

    # Настройки уведомлений
    notify_assigned = Column(Boolean, default=True)
    notify_overdue = Column(Boolean, default=True)
    
    # Аукцион и бюджет
    budget = Column(Float, nullable=True)  # Бюджет задачи
    category_code = Column(String(255), nullable=True)
    work_category = Column(String(255), nullable=True)  # Категория задачи  # Категория затрат
    source_auction_id = Column(String(36), ForeignKey("task_auctions.id"), nullable=True)
    executor_rating = Column(Integer, nullable=True)  # Оценка исполнителя 1-5
    
    # Расчёт штрафов/бонусов (фиксируются при завершении)
    final_budget = Column(Float, nullable=True)  # Итоговый бюджет после коэффициентов
    rating_coefficient = Column(Float, nullable=True)  # Коэффициент за оценку
    deadline_coefficient = Column(Float, nullable=True)  # Коэффициент за сроки
    penalty_amount = Column(Float, nullable=True)  # Сумма штрафа (- бонус)

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    deal = relationship("Deal", backref="tasks")
    stage = relationship("Stage", backref="tasks")
    assigned_to = relationship("Company", foreign_keys=[assigned_to_id])
    created_by = relationship("Company", foreign_keys=[created_by_id])
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    payer = relationship("Company", foreign_keys=[payer_id])
    payee = relationship("Company", foreign_keys=[payee_id])
    income_expense = relationship("IncomeExpenseEntry", foreign_keys=[income_expense_id])

    # M2M: исполнители (множественные) и наблюдатели
    assignee_links = relationship(
        "TaskAssignee",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    watcher_links = relationship(
        "TaskWatcher",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        """Получить все задачи"""
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, task_id: str):
        """Получить задачу по ID"""
        from sqlalchemy import select
        try:
            task_uuid = task_id if isinstance(task_id, uuid.UUID) else uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            task_uuid = None
        task_id_str = str(task_uuid) if task_uuid else str(task_id)
        query = select(cls).where(cls.id == task_id_str)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_deal_id(cls, db, deal_id: str):
        """Получить все задачи проекта"""
        from sqlalchemy import select
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            deal_uuid = None
        deal_id_str = str(deal_uuid) if deal_uuid else str(deal_id)
        query = select(cls).where(cls.deal_id == deal_id_str).order_by(cls.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_assigned_to(cls, db, assigned_to_id: str):
        """Получить задачи назначенные пользователю"""
        from sqlalchemy import select
        try:
            assigned_uuid = assigned_to_id if isinstance(assigned_to_id, uuid.UUID) else uuid.UUID(str(assigned_to_id))
        except (ValueError, TypeError):
            assigned_uuid = None
        assigned_id_str = str(assigned_uuid) if assigned_uuid else str(assigned_to_id)
        query = select(cls).where(cls.assigned_to_id == assigned_id_str).order_by(cls.due_date.asc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новую задачу"""
        from datetime import datetime
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        # Normalize UUIDs for SQLite and remove None values.
        processed_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, uuid.UUID):
                processed_kwargs[key] = str(value)
            else:
                processed_kwargs[key] = value
        processed_kwargs = {k: v for k, v in processed_kwargs.items() if v is not None}
        task = cls(**processed_kwargs)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @classmethod
    async def update(cls, db, task_id: str, **kwargs):
        """Обновить задачу"""
        from sqlalchemy import update
        try:
            task_uuid = task_id if isinstance(task_id, uuid.UUID) else uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            task_uuid = None
        task_id_str = str(task_uuid) if task_uuid else str(task_id)
        
        # Convert UUID objects to strings for SQLite compatibility
        processed_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, uuid.UUID):
                processed_kwargs[key] = str(value)
            else:
                processed_kwargs[key] = value
        
        query = (
            update(cls)
            .where(cls.id == task_id_str)
            .values(**processed_kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, task_id)

    @classmethod
    async def delete(cls, db, task_id: str) -> bool:
        """Удалить задачу"""
        from sqlalchemy import delete
        try:
            task_uuid = task_id if isinstance(task_id, uuid.UUID) else uuid.UUID(str(task_id))
        except (ValueError, TypeError):
            task_uuid = None
        task_id_str = str(task_uuid) if task_uuid else str(task_id)
        query = delete(cls).where(cls.id == task_id_str)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
