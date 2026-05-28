"""UserAbsence — отсутствие сотрудника (отпуск/больничный/командировка/др.).

Одна строка = один интервал отсутствия с типом и комментарием.
Период полузакрытый по календарю: `date_from` и `date_to` включительно
(оба — даты без времени; для удобного отображения «с 12 по 20 мая»).

Кто видит: все авторизованные (раздел `absences`, read_all).
Кто правит:
- свои — сам пользователь (`edit_assigned` на секции `absences`);
- чужие — только админ с `edit_all`.
"""
import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


# Допустимые типы. Расширяется при необходимости — добавить значение
# сюда + варианты в frontend ABSENCE_TYPES (для лейблов и цветов).
ABSENCE_TYPES = ("vacation", "sick_leave", "business_trip", "other")


class UserAbsence(Base):
    __tablename__ = "user_absences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Один из ABSENCE_TYPES. Проверка на уровне Pydantic-схемы.
    type = Column(String(20), nullable=False)
    # Обе даты включительно. Хранятся как Date, без времени.
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    comment = Column(Text, nullable=True)

    # Кто создал запись (может отличаться от user_id — админ за коллегу).
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        # Быстрая выборка «у кого сейчас отсутствие» по дате.
        Index("ix_user_absences_dates", "date_from", "date_to"),
        Index("ix_user_absences_user_dates", "user_id", "date_from"),
    )
