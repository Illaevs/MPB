"""
Обработчики для лидов.

Особый кейс — `lead.before_convert_to_deal`: проверяем, что лид готов
к конверсии (есть контактные данные, не дубль, не отклонён).
"""
from __future__ import annotations

import logging

from app.services.event_dispatcher import (
    Cancel,
    Continue,
    EventContext,
    Mutate,
    on,
)

logger = logging.getLogger(__name__)


@on("lead.before_convert_to_deal", priority=100, can_cancel=True)
async def validate_lead_ready_for_conversion(ctx: EventContext):
    """Запрещает конверсию лида без обязательных полей."""
    if not ctx.payload.get("title") and not ctx.payload.get("name"):
        return Cancel(
            "У лида не указано название/имя — конвертация невозможна",
            code="lead.no_title",
        )
    status = ctx.payload.get("status")
    if status in {"rejected", "lost", "duplicate"}:
        return Cancel(
            f"Лид в статусе «{status}» — конверсия запрещена",
            code="lead.bad_status",
        )
    return Continue()


@on("lead.before_convert_to_deal", priority=90, can_mutate=True)
async def stamp_source_lead_id(ctx: EventContext):
    """Прокидываем в будущую сделку id исходного лида — для трассировки."""
    if ctx.entity_id and "source_lead_id" not in ctx.payload:
        return Mutate(payload_patch={"source_lead_id": ctx.entity_id})
    return Continue()


@on("lead.before_create", priority=100, can_cancel=True)
async def validate_new_lead(ctx: EventContext):
    """При создании лида проверяем минимально-обязательные поля."""
    title = (ctx.payload.get("title") or "").strip()
    if not title:
        return Cancel("Не указано название лида", code="lead.no_title")
    return Continue()


@on("lead.before_status_change", priority=100, can_cancel=True)
async def validate_lead_status_transition(ctx: EventContext):
    """Терминальные статусы (rejected/lost/converted) — не возвращаются назад."""
    old = ctx.payload.get("status_before")
    new = ctx.payload.get("status_after")
    if old in {"converted", "rejected", "lost", "duplicate"} and old != new:
        return Cancel(
            f"Лид в терминальном статусе «{old}» — переход в «{new}» запрещён",
            code="lead.terminal_status",
        )
    return Continue()
