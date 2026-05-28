"""
Обработчики для документов реестра документации (`document` сущность).

State-machine: draft → sent → received → archived / rejected.
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


@on("document.before_send", priority=100, can_cancel=True)
async def validate_before_send(ctx: EventContext):
    """Нельзя отправить документ, у которого нет файла-носителя."""
    if not ctx.payload.get("file_path") and not ctx.payload.get("storage_url"):
        return Cancel(
            "Нельзя отправить документ без приложенного файла",
            code="document.no_file",
        )
    if not ctx.payload.get("channel"):
        return Cancel(
            "Не указан канал отправки (email/Диадок/курьер)",
            code="document.no_channel",
        )
    return Continue()


@on("document.before_status_change", priority=100, can_cancel=True)
async def validate_status_progression(ctx: EventContext):
    """Запрещает заведомо неправильные переходы (например, archived → draft)."""
    new = ctx.payload.get("status_after")
    old = ctx.payload.get("status_before")
    # Терминальные статусы — назад нельзя.
    if old in {"archived", "rejected"} and new not in {"archived", "rejected"}:
        return Cancel(
            f"Нельзя вернуть документ из «{old}» в «{new}»",
            code="document.terminal_status",
        )
    return Continue()
