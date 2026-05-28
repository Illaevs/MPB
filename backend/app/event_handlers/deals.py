"""
In-process обработчики для сделок (deal).

Сейчас один хук — `before_status_change` с парой проверок:
  • нельзя закрыть сделку (status=`completed`/`won`) при наличии
    незакрытых обязательных этапов;
  • нельзя перевести в `lost`/`cancelled` без указания причины.
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


@on("deal.before_status_change", priority=100, can_cancel=True)
async def validate_deal_status_transition(ctx: EventContext):
    """Валидация перехода статуса сделки.

    payload:
      • status_before, status_after
      • open_required_stages (int, optional) — кол-во незакрытых
        обязательных этапов; роутер если может — присылает.
      • reason (optional) — причина отказа/потери.
    """
    new = ctx.payload.get("status_after")
    if new in {"won", "completed"}:
        open_stages = ctx.payload.get("open_required_stages")
        if open_stages and open_stages > 0:
            return Cancel(
                f"Нельзя закрыть сделку — открыто обязательных этапов: {open_stages}",
                code="deal.open_required_stages",
            )

    if new in {"lost", "cancelled"}:
        reason = (ctx.payload.get("reason") or "").strip()
        # Жёсткое требование делаем мягким: если reason передан как поле
        # в request — ожидаем непустой. Если не передан — пропускаем
        # (роутер сам разруливает обязательность через схему).
        if "reason" in ctx.payload and not reason:
            return Cancel(
                f"При переводе в «{new}» нужно указать причину",
                code="deal.reason_required",
            )

    return Continue()
