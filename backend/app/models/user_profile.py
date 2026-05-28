"""UserProfile — расширенная карточка сотрудника.

Отдельная таблица 1-к-1 с `users` (а не JSON-поле), чтобы держать
ссылочную целостность для `manager_id` и сохранить возможность
индексных выборок (директория «кто есть кто», поиск по навыкам).

Поля делятся на две группы по правам:
- ФОРМАЛЬНЫЕ (правит только админ):
  `job_title`, `department`, `manager_id`, `hire_date`.
- ЛИЧНЫЕ (правит сам владелец + админ):
  `birth_date`, `birth_show_year`, `bio`, `interests`, `skills`,
  `telegram_username`.

Видимость — публичная (все авторизованные видят весь профиль).
"""
import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # --- ФОРМАЛЬНЫЕ (правит только админ) ---
    job_title = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    manager_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    hire_date = Column(Date, nullable=True)

    # --- ЛИЧНЫЕ (правит сам + админ) ---
    birth_date = Column(Date, nullable=True)
    # Юзер может скрыть год в публичной выдаче (показывать только дд.мм).
    birth_show_year = Column(Boolean, default=True, nullable=False)
    bio = Column(Text, nullable=True)
    # Свободный ввод чипами. Автокомплит из суггеста по всем профилям.
    interests = Column(JSON, default=list, nullable=False)
    skills = Column(JSON, default=list, nullable=False)
    telegram_username = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="profile",
    )
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
    )
