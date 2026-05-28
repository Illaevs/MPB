"""
Обработчики для процесса согласования (approval_instance).

State-machine: started → in_progress → (approved | rejected | cancelled).
Каждый шаг (approval_instance_step) тоже имеет свой жизненный цикл.
"""
from __future__ import annotations

import logging

from app.services.event_dispatcher import (
    Cancel,
    Continue,
    EventContext,
    on,
)

logger = logging.getLogger(__name__)


@on("approval_instance.before_complete", priority=100, can_cancel=True)
async def require_all_steps_done(ctx: EventContext):
    """Нельзя завершить согласование, пока не все шаги пройдены.

    Бэкенд кладёт в payload `unresolved_steps_count` — счётчик шагов,
    которые не в финальном статусе.
    """
    unresolved = ctx.payload.get("unresolved_steps_count", 0)
    if unresolved and unresolved > 0:
        return Cancel(
            f"Остались незавершённые шаги ({unresolved}). Сначала закройте их.",
            code="approval.unresolved_steps",
        )
    return Continue()


@on("approval_instance.before_reject", priority=100, can_cancel=True)
async def require_reject_reason(ctx: EventContext):
    """Отклонение согласования всегда должно сопровождаться причиной —
    иначе пользователь не поймёт, что исправить.
    """
    if not (ctx.payload.get("reason") or "").strip():
        return Cancel(
            "Укажите причину отклонения",
            code="approval.reason_required",
        )
    return Continue()
