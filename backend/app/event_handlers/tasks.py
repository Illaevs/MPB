"""
In-process обработчики для задач.

Сейчас два хука:
  • `task.before_status_change` — запрет некорректных переходов;
  • `task.before_assign` — валидация исполнителя (например, нельзя
    назначить уволенного юзера).

Расширяется новыми правилами в одном файле.
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


@on("task.before_status_change", priority=100, can_cancel=True)
async def validate_task_status_transition(ctx: EventContext):
    """Запрещает заведомо некорректные переходы статусов задачи.

    payload:
      • status_before — текущий
      • status_after  — желаемый
      • completed_subtasks / total_subtasks — для completed

    Правила:
      1. completed когда есть незавершённые подзадачи — Cancel.
         (Чтобы случайно не закрыть задачу с открытыми пунктами.)
      2. cancelled из completed — Cancel (терминальный → терминальный
         запрещён, нужно сначала reopen).
    """
    new = ctx.payload.get("status_after")
    old = ctx.payload.get("status_before")

    if new == "completed":
        total = ctx.payload.get("total_subtasks") or 0
        done = ctx.payload.get("completed_subtasks") or 0
        if total > 0 and done < total:
            return Cancel(
                f"Нельзя завершить задачу с открытыми подзадачами ({done}/{total}). "
                "Сначала закройте все пункты или удалите лишние.",
                code="task.completed_with_open_subtasks",
            )

    if old in {"completed", "cancelled"} and new == "cancelled":
        return Cancel(
            f"Нельзя перевести в «отменено» из «{old}». Сначала reopen.",
            code="task.terminal_to_cancelled",
        )

    return Continue()


@on("task.before_assign", priority=100, can_cancel=True)
async def validate_task_assignee(ctx: EventContext):
    """Проверяет валидность нового исполнителя.

    payload:
      • assigned_to_user_id — кому назначаем
      • assignee_is_active — bool, активен ли юзер (роутер должен
        прислать; если нет — пропускаем проверку, не блокируем).
    """
    user_id = ctx.payload.get("assigned_to_user_id")
    if not user_id:
        return Continue()
    active = ctx.payload.get("assignee_is_active")
    if active is False:
        return Cancel(
            "Нельзя назначить задачу на отключённого пользователя",
            code="task.assignee_inactive",
        )
    return Continue()
