"""Pydantic-схемы для эндпоинтов учёта рабочего времени."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# Дефолтный idle-таймаут, если в роли idle_timeout_minutes == NULL.
DEFAULT_IDLE_TIMEOUT_MINUTES = 30


class WorkSessionResponse(BaseModel):
    """Одна сессия учёта (активная или закрытая)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    ended_reason: Optional[str] = None  # 'manual' | 'idle' | 'admin'
    last_activity_at: datetime
    note_start: Optional[str] = None
    note_end: Optional[str] = None
    duration_seconds: int = 0
    is_active: bool = False


class WorkdayActiveResponse(BaseModel):
    """Состояние «рабочего дня» для текущего пользователя.

    `session` — активная сейчас (или null, если не начат). FE по нему
    решает: показать модал «Начать рабочий день» или счётчик в топбаре.
    `track_work_time` — выключатель фичи для роли (если False, FE
    вообще ничего не показывает по учёту). `idle_timeout_minutes` —
    через сколько минут бездействия фронт сам закрывает сессию (с
    отметкой `ended_at = last_activity_at`, причина `idle`).

    `worked_today_seconds` — сумма ЗАКРЫТЫХ сессий за сегодняшний день
    по московской дате (UTC+3 без DST). Фронт прибавляет к этому числу
    live-elapsed активной сессии — чтобы счётчик в чипе показывал не
    отдельный отрезок, а накопленный итог за день. Атрибуция по
    `started_at`: сессия попадает в день своего начала."""
    session: Optional[WorkSessionResponse] = None
    track_work_time: bool = False
    idle_timeout_minutes: int = DEFAULT_IDLE_TIMEOUT_MINUTES
    worked_today_seconds: int = 0


class WorkdayStartRequest(BaseModel):
    note_start: Optional[str] = Field(default=None, max_length=4000)


class WorkdayEndRequest(BaseModel):
    # 'manual' (нажал кнопку) | 'idle' (фронт сам закрыл по бездействию).
    reason: str = Field(default="manual", pattern="^(manual|idle)$")
    # Для reason='idle': FE передаёт точное время последней активности —
    # его и пишем в ended_at. Для manual поле не нужно.
    ended_at: Optional[datetime] = None
    note_end: Optional[str] = Field(default=None, max_length=4000)


class WorkdayHeartbeatResponse(BaseModel):
    """Возвращает обновлённый last_activity_at либо null если сессии нет."""
    session_id: Optional[str] = None
    last_activity_at: Optional[datetime] = None


# ---- Stats schemas (phase 3) ---------------------------------------------

class WorkdayListItem(BaseModel):
    """Строка для боковой панели статистики: один пользователь + его
    суммарное время за период (для админа — все юзеры, иначе только себя).

    `worked_today` — был ли у юзера хотя бы один тик активности
    в сегодняшний день (server UTC). Используется фронтом, чтобы
    подсветить «не был сегодня» в сайдбаре независимо от фильтра дат."""
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None
    total_seconds: int = 0
    sessions_count: int = 0
    has_active: bool = False
    worked_today: bool = False


class WorkdayGridItem(BaseModel):
    """Строка табличного вида: один сотрудник + посуточная разбивка
    отработанных секунд за период.

    `days` — карта `ISO-дата → секунды` (только дни, где что-то было).
    Сессия атрибутируется дню своего `started_at` (как в /stats day)."""
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None
    total_seconds: int = 0
    has_active: bool = False
    days: dict[str, int] = {}


class WorkdayBucket(BaseModel):
    """Период (день/неделя/месяц) с агрегатом и сессиями."""
    key: str  # ISO дата дня '2026-05-20' или '2026-W21' / '2026-05'
    label: str
    total_seconds: int = 0
    sessions: list[WorkSessionResponse] = []


class WorkdayStatsResponse(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None
    total_seconds: int = 0
    sessions_count: int = 0
    buckets: list[WorkdayBucket] = []


class WorkdaySessionPatch(BaseModel):
    """Админ-правка существующей сессии."""
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    ended_reason: Optional[str] = Field(default=None, pattern="^(manual|idle|admin)$")
    note_start: Optional[str] = Field(default=None, max_length=4000)
    note_end: Optional[str] = Field(default=None, max_length=4000)
