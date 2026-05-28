"""
In-process обработчики для исходящих документов (outgoing_document).

State-machine: draft → review → ready → sent → ack.
Render — побочная фаза (генерация PDF/DOCX); прежде чем рендерить,
нужно убедиться что обязательные поля заполнены.
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


@on("outgoing_document.before_render", priority=100, can_cancel=True)
async def validate_required_fields(ctx: EventContext):
    """Запрещает рендер пока не заполнены обязательные поля для
    выбранного типа документа.

    Минимальный универсальный набор: должен быть проставлен `document_kind`
    и (если это не invoice) — `recipient`. Для конкретных типов (Диадок,
    счёт-фактура) добавляем правила в той же функции — НЕ редиректами.
    """
    kind = ctx.payload.get("document_kind")
    if not kind:
        return Cancel("Не указан тип исходящего документа", code="outgoing.kind_missing")
    if kind not in {"invoice", "internal_memo"} and not ctx.payload.get("recipient"):
        return Cancel(
            "Не указан получатель документа",
            code="outgoing.recipient_missing",
        )
    return Continue()


@on("outgoing_document.before_render", priority=90, can_mutate=True)
async def stamp_render_meta(ctx: EventContext):
    """Перед рендером добавляем мета: кто/когда инициировал. Эти поля
    кладутся в payload, оттуда — в render-context, оттуда — в шаблон.
    """
    if ctx.user_id and "rendered_by" not in ctx.payload:
        return Mutate(payload_patch={"rendered_by": ctx.user_id})
    return Continue()
