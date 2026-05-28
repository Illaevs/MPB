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

# V1.5: цепочка причинности (event_id предков) — пробрасывается через
# contextvar, чтобы вложенный обработчик мог записать «я родился из A,
# который родился из B, ...» без явной передачи аргументом. Worker
# выставляет это перед вызовом in-process handlers.
_causation_chain: contextvars.ContextVar[List[str]] = contextvars.ContextVar(
    "event_outbox_causation_chain", default=[]
)

# Граница глубины цепочки — выше неё emit отказывается работать.
# Защищает от непреднамеренных циклов «notification → event_log →
# notification → ...». Можно переопределить через ENV в worker'е.
MAX_CAUSATION_DEPTH = 5


# ────────────────────────────────────────────────────────────────────
# In-process after-emit hooks (для wildcard-консьюмеров вроде индексера).
#
# Зачем:
#   Большинство `emit_event_safe` в роутерах НЕ проходит через
#   `dispatch_after`, поэтому декораторный `@on("entity.action")` не
#   ловит их. А consumer'у поиска нужно реагировать на ВСЁ
#   (`*.after_create/update/delete`), без правок каждого роутера.
#
# Решение:
#   Любой модуль может зарегистрировать callback через
#   `register_after_emit_hook(fn)`. После успешного `await db.flush()`
#   все hooks вызываются с (db, EventOutbox-row).
#   Hook сам решает по `row.event_type`, реагировать ли.
#
# Гарантии:
#   • Hook вызывается ПОСЛЕ flush (item.id уже есть), но ДО commit
#     бизнес-транзакции — индексация в одной транзакции с бизнес-данными.
#   • Hook падает → ошибка ловится, остальные hooks продолжают работу
#     (soft-fail, как in-process after-handlers в dispatcher).
#   • Hook НЕ блокирует emit, если что-то пошло не так.
# ────────────────────────────────────────────────────────────────────

_AFTER_EMIT_HOOKS: List[Any] = []


def register_after_emit_hook(callback) -> None:
    """Зарегистрировать callback, который будет вызван после каждого
    успешного emit_event. Callback: `async def hook(db, outbox_row) -> None`.

    Вызывается из `main.py` startup — один раз на процесс."""
    _AFTER_EMIT_HOOKS.append(callback)


async def _fire_after_emit_hooks(db: AsyncSession, row) -> None:
    """Вызвать все зарегистрированные hooks. Soft-fail."""
    for hook in _AFTER_EMIT_HOOKS:
        try:
            result = hook(db, row)
            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            logger.warning(
                "after_emit hook %s raised: %s",
                getattr(hook, "__qualname__", str(hook)), exc, exc_info=True,
            )


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
    causation_chain: Optional[List[str]] = None,
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
            обработчика (по умолчанию подавляем — boolean recursion guard
            из V1, оставлен для обратной совместимости).
        causation_chain: явный список event_id предков; если не передан,
            берётся из contextvar (worker выставляет его перед обработкой
            in-process handler'а). При превышении MAX_CAUSATION_DEPTH —
            WARN + no-op (защита от глубоких циклов).
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

    # V1.5 causation chain: явный аргумент имеет приоритет, иначе берём
    # из contextvar (worker выставляет его перед вызовом обработчика).
    effective_chain: List[str] = list(
        causation_chain if causation_chain is not None else _causation_chain.get()
    )
    if len(effective_chain) >= MAX_CAUSATION_DEPTH:
        # Глубокая цепочка — подозрение на цикл. Всегда отказываем,
        # независимо от allow_recursion: defence-in-depth.
        logger.warning(
            "Event causation depth %d >= %d, skipping emit %s entity=%s/%s chain=%s",
            len(effective_chain), MAX_CAUSATION_DEPTH,
            event_type, entity_type, entity_id, effective_chain,
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
        causation_chain=effective_chain or None,
    )
    db.add(item)
    # flush — чтобы id сразу появился у item; commit делает вызывающий.
    await db.flush()
    # In-process hooks — wildcard-консьюмеры (индексер поиска и т.п.).
    # Soft-fail: ошибка в hook не валит emit.
    await _fire_after_emit_hooks(db, item)
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


async def emit_batch_event(
    db: AsyncSession,
    *,
    event_type: str,
    entity_type: str,
    items: List[Dict[str, Any]],
    parent_id: Optional[str] = None,
    summary: Optional[Dict[str, Any]] = None,
    payload_version: int = 1,
) -> Optional[EventOutbox]:
    """Эмитирует ОДНО batch-событие вместо N штук.

    Используется для импортов (банк-выписка, 1С-выгрузка, СОДы):
    подписчик получает «вот пачка из 500 транзакций» одним POST'ом,
    обрабатывает группой — это быстрее (нет 500 round-trip'ов) и
    атомарнее (либо вся пачка ушла, либо её ретраим целиком).

    Конвенция event_type: `{entity}.batch_{action}` —
        treasury_transaction.batch_imported
        contract.batch_signed
        outgoing_document.batch_sent

    `entity_id` outbox-записи — `parent_id` (если есть, например id
    job'а импорта) или специальная константа `__batch__`. Реальный
    список id-шек лежит в payload.items[].id.

    `summary` — опциональный агрегат (например, total_amount=...,
    matched_count=12, errors=0). Удобно для UI/мониторинга без
    разворачивания items[].
    """
    safe_items = list(items or [])
    payload = {
        "items": safe_items,
        "items_count": len(safe_items),
        "summary": summary or {},
        "parent_id": parent_id,
    }
    return await emit_event(
        db,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(parent_id or "__batch__"),
        payload=payload,
        payload_version=payload_version,
    )


async def emit_batch_event_safe(db: AsyncSession, **kwargs) -> Optional[EventOutbox]:
    """Defensive обёртка над emit_batch_event."""
    try:
        return await emit_batch_event(db, **kwargs)
    except Exception as exc:  # pragma: no cover
        logger.warning("emit_batch_event_safe swallowed: %s", exc, exc_info=True)
        return None


from contextlib import contextmanager


@contextmanager
def causation_scope(parent_event_id: str):
    """Контекст-менеджер для in-process post-handler'ов (worker-side).

    Использование:
        with causation_scope(row.event_id):
            await handler(row)        # любой emit внутри получит
                                       # причину = текущая цепочка + row.event_id

    Гарантирует корректное восстановление contextvar даже при исключении.
    """
    token = _causation_chain.set(list(_causation_chain.get()) + [str(parent_event_id)])
    try:
        yield
    finally:
        _causation_chain.reset(token)


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


def _parse_condition_json(raw: Any) -> Any:
    """Нормализует condition_json: SQLite иногда возвращает str, иногда dict."""
    if raw is None or raw == "" or raw == {}:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return None
    return raw


async def simulate_subscription_match(
    db: AsyncSession,
    event_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """DRY-RUN: какие подписки получили бы это событие, и какие — нет.

    Используется в `POST /event-bus/simulate` для отладки condition_json
    и pattern'ов. НЕ создаёт outbox-записей, НЕ отправляет webhook'и.

    Возвращает:
        {
          "matched": [{id, name, target_url, matched_by, condition_json}],
          "skipped": [{id, name, reason, condition_json}],
        }
    """
    from app.services.json_logic import evaluate as _eval_condition

    pattern_matched = await list_matching_subscriptions(db, event_type)
    matched: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for sub in pattern_matched:
        sub_info = {
            "id": str(sub.id),
            "name": sub.name,
            "target_url": sub.target_url,
            "event_type_pattern": sub.event_type_pattern,
        }
        cond = _parse_condition_json(getattr(sub, "condition_json", None))
        sub_info["condition_json"] = cond
        if cond is None:
            sub_info["matched_by"] = f"pattern '{sub.event_type_pattern}'"
            matched.append(sub_info)
            continue
        try:
            ok = _eval_condition(cond, payload or {})
        except Exception as exc:
            sub_info["reason"] = f"condition evaluation error: {exc}"
            skipped.append(sub_info)
            continue
        if ok:
            sub_info["matched_by"] = f"pattern '{sub.event_type_pattern}' + condition_json matched"
            matched.append(sub_info)
        else:
            sub_info["reason"] = "condition_json mismatch"
            skipped.append(sub_info)

    # Полный список подписок (включая те, чей pattern не сматчился) —
    # это полезно UI'у: «вот всё что есть, вот сколько включено в этот
    # event, сколько отвалилось».
    all_rows = (await db.execute(
        select(EventSubscription).where(EventSubscription.is_active == True)
    )).scalars().all()
    matched_ids = {sub["id"] for sub in matched}
    skipped_ids = {sub["id"] for sub in skipped}
    for sub in all_rows:
        sid = str(sub.id)
        if sid in matched_ids or sid in skipped_ids:
            continue
        skipped.append({
            "id": sid,
            "name": sub.name,
            "target_url": sub.target_url,
            "event_type_pattern": sub.event_type_pattern,
            "condition_json": _parse_condition_json(getattr(sub, "condition_json", None)),
            "reason": f"pattern '{sub.event_type_pattern}' does not match '{event_type}'",
        })

    return {"matched": matched, "skipped": skipped}


def serialize_outbox_row(row: EventOutbox) -> Dict[str, Any]:
    """Сериализация строки outbox для API-ответа и для worker-логов."""
    payload = row.payload
    if isinstance(payload, str):
        try: payload = json.loads(payload)
        except Exception: payload = {}
    # causation_chain — может прийти как list, как str (старые записи) или None.
    chain = row.causation_chain
    if isinstance(chain, str):
        try: chain = json.loads(chain)
        except Exception: chain = []
    if chain is None:
        chain = []
    return {
        "id": str(row.id),
        "event_id": str(row.event_id),
        "event_type": row.event_type,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "payload": payload or {},
        "payload_version": row.payload_version,
        "causation_chain": list(chain),
        "status": row.status,
        "attempt_count": row.attempt_count,
        "last_error": row.last_error,
        "scheduled_at": row.scheduled_at.isoformat() if row.scheduled_at else None,
        "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
