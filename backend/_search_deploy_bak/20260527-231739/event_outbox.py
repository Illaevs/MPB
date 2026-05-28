"""
Сервис emit_event — единственная точка входа для записи бизнес-событий
в outbox-таблицу.  Вызывается роутерами сразу после успешной записи
бизнес-данных, ДО commit/завершения транзакции — чтобы бизнес-факт и
запись об уведомлении ушли атомарно (outbox pattern).

Закрывает требования v2-спека event bus:
  • idempotency — параметр `event_id` опционален; если передан, повтор
    с тем же id — no-op (используется при ручных ретраях извне).
  • recursion guard — contextvars-флаг `_in_emit` блокирует вложенные
    emit-ы внутри текущего обработчика; чтобы пробросить мета-событие,
    подписчик явно делает `allow_recursion=True`.
  • ordering per entity — мы только записываем; реальный порядок
    выдерживает воркер (sort by entity_type, entity_id, created_at).
  • schema versioning — `payload_version` пишется в строку, подписчик
    разруливает совместимость на своей стороне.

Что НЕ закрываем здесь:
  • batch-семантика — будет добавлена через emit_batch(...) в Spec v2;
  • DSL для conditions — отдельный сервис condition_eval;
  • error semantics в-after хендлеров — это policy worker'а, не emit.
"""
import contextvars
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EventOutbox, EventSubscription

logger = logging.getLogger(__name__)

# Recursion guard. Если внутри обработки события (например, в подписке
# на deal.after_create) случайно начнут эмитить новые события — мы
# зафиксируем флаг и подавим запись.  Подписчик, которому это нужно
# (мета-каскад, ручной opt-in), вызовет emit_event(..., allow_recursion=True).
_in_emit: contextvars.ContextVar[bool] = contextvars.ContextVar("event_outbox_in_emit", default=False)


async def emit_event(
    db: AsyncSession,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload: Optional[Dict[str, Any]] = None,
    payload_version: int = 1,
    event_id: Optional[str] = None,
    allow_recursion: bool = False,
) -> Optional[EventOutbox]:
    """Записать событие в outbox.  Возвращает созданную строку или None.

    Бросает только программные ошибки (неправильные аргументы); сетевые
    проблемы доставки — это уже ответственность воркера и они происходят
    позже, не блокируют бизнес-транзакцию.

    Args:
        db: текущая async-сессия (одна транзакция с бизнес-данными).
        event_type: "<entity>.<action>" — например "deal.after_create".
        entity_type, entity_id: для ordering per entity и для отладки в UI.
        payload: dict, попадёт в JSON-колонку и будет доставлен подписчику.
        payload_version: версия схемы payload для будущих миграций.
        event_id: опциональный явный id события (для idempotency на
            стороне вызывающего, например при ручном retry).
        allow_recursion: позволить эмит из контекста уже активного
            обработчика (по умолчанию подавляем — recursion guard).
    """
    if not event_type or not entity_type or not entity_id:
        raise ValueError("event_type, entity_type, entity_id are required")

    if _in_emit.get() and not allow_recursion:
        # Тихий no-op — самый частый случай, когда хук случайно вызывает
        # emit; явный allow_recursion=True нужен только для мета-каскадов.
        logger.debug(
            "Recursion guard suppressed emit %s entity=%s/%s",
            event_type, entity_type, entity_id,
        )
        return None

    resolved_event_id = str(event_id) if event_id else str(uuid.uuid4())

    # Idempotency: если строка с таким event_id уже есть — повтор no-op.
    existing = (
        await db.execute(select(EventOutbox).where(EventOutbox.event_id == resolved_event_id))
    ).scalar_one_or_none()
    if existing:
        logger.debug("emit_event idempotent skip event_id=%s", resolved_event_id)
        return existing

    item = EventOutbox(
        id=str(uuid.uuid4()),
        event_id=resolved_event_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        payload=payload or {},
        payload_version=int(payload_version or 1),
        status="pending",
        attempt_count=0,
    )
    db.add(item)
    # flush — чтобы id сразу появился у item; commit делает вызывающий.
    await db.flush()
    return item


async def emit_event_safe(db: AsyncSession, **kwargs) -> Optional[EventOutbox]:
    """Обёртка, которая глотает любые исключения emit_event и
    логирует их.  Использовать в роутерах, где бизнес-операция не
    должна падать из-за проблемы outbox-пайплайна."""
    try:
        return await emit_event(db, **kwargs)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("emit_event_safe swallowed error: %s", exc, exc_info=True)
        return None


# =====================================================================
# Helpers для воркера и роутеров event-bus (не вызываются из бизнес-кода)
# =====================================================================


def _compile_pattern(pattern: str) -> re.Pattern:
    """`deal.*` -> regex `^deal\\..*$`. `*` -> `^.*$`. Точка экранируется."""
    escaped = re.escape(pattern.strip()).replace(r"\*", ".*")
    return re.compile("^" + escaped + "$")


async def list_matching_subscriptions(
    db: AsyncSession,
    event_type: str,
) -> List[EventSubscription]:
    """Активные подписки, чьи паттерны матчат данный event_type."""
    rows = (await db.execute(
        select(EventSubscription).where(EventSubscription.is_active == True)
    )).scalars().all()
    out: List[EventSubscription] = []
    for sub in rows:
        try:
            if _compile_pattern(sub.event_type_pattern or "").match(event_type):
                out.append(sub)
        except re.error:
            logger.warning("Invalid pattern in subscription %s: %r", sub.id, sub.event_type_pattern)
    return out


def serialize_outbox_row(row: EventOutbox) -> Dict[str, Any]:
    """Сериализация строки outbox для API-ответа и для worker-логов."""
    payload = row.payload
    if isinstance(payload, str):
        try: payload = json.loads(payload)
        except Exception: payload = {}
    return {
        "id": str(row.id),
        "event_id": str(row.event_id),
        "event_type": row.event_type,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "payload": payload or {},
        "payload_version": row.payload_version,
        "status": row.status,
        "attempt_count": row.attempt_count,
        "last_error": row.last_error,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
        "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
