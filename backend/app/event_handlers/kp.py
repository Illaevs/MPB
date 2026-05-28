"""
Обработчики коммерческих предложений (kp_document).

Перед рендером — обязательная привязка к лиду + наличие хотя бы одной
строки таблицы товаров/услуг.
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


@on("kp_document.before_render", priority=100, can_cancel=True)
async def validate_kp_ready(ctx: EventContext):
    if not ctx.payload.get("lead_id"):
        return Cancel("КП не привязано к лиду", code="kp.no_lead")
    items_count = ctx.payload.get("items_count")
    if items_count is not None and items_count == 0:
        return Cancel(
            "В КП нет ни одной позиции — рендер невозможен",
            code="kp.empty_items",
        )
    return Continue()
