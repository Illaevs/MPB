"""WorkSession model — учёт рабочего времени пользователя.

Одна строка = одна сессия «рабочий день / часть дня». Сессия живёт,
пока `ended_at IS NULL`. Закрывается:
- вручную пользователем (`ended_reason = 'manual'`),
- авто по бездействию (`ended_reason = 'idle'`),
- админом из раздела статистики (`ended_reason = 'admin'`).

`last_activity_at` обновляется heartbeat'ом раз в 60 секунд, пока
пользователь активно работает. При автозакрытии `ended_at` ставится
равным именно `last_activity_at` (а не моменту срабатывания таймера) —
так в зачёт не идёт время пассивного простоя.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class WorkSession(Base):
    __tablename__ = "work_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    # 'manual' | 'idle' | 'admin' (NULL пока сессия активна)
    ended_reason = Column(String(16), nullable=True)

    # Обновляется heartbeat'ом каждые ~60 секунд + при любом /workday-эндпоинте.
    last_activity_at = Column(DateTime(timezone=True), nullable=False)

    # Опциональные заметки. На MVP — необязательные строки.
    note_start = Column(Text, nullable=True)
    note_end = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_work_sessions_user_started", "user_id", "started_at"),
        # Активная сессия у пользователя; ускоряет поиск «is there an open one».
        Index("ix_work_sessions_user_active", "user_id", "ended_at"),
    )

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def duration_seconds(self) -> int:
        """Длительность сессии в секундах.

        Для активной — от started_at до last_activity_at (а не до now() —
        отсутствие активности тоже не считается работой). Для закрытой —
        от started_at до ended_at."""
        end = self.ended_at or self.last_activity_at or self.started_at
        start = self.started_at
        if not end or not start:
            return 0
        return int((end - start).total_seconds())
