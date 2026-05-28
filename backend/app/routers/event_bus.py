"""
API роутер event bus: чтение outbox, ручной retry, CRUD подписок,
test-sink для smoke-проверки доставки.

Доступ к management-эндпоинтам — только суперюзер (is_superuser сидит
в request.state, проставляется auth_middleware).
Test-sink открыт без auth — это синтетический приёмник для прогона
сценариев из локалки (см. CSRF_EXEMPT_PATHS и AuthMiddleware open_paths).
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import EventOutbox, EventSubscription, EventDeliveryDedup, User
from app.schemas.event_bus import (
    EventOutboxResponse,
    EventSubscriptionCreate,
    EventSubscriptionResponse,
    EventSubscriptionUpdate,
)
from app.services.event_outbox import serialize_outbox_row, list_matching_subscriptions

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_superuser(request: Request):
    """is_superuser ставится auth_middleware в request.state, на User
    модели такого атрибута НЕТ — проверять надо именно через request."""
    if not getattr(request.state, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Superuser required")


# =====================================================================
# Outbox: чтение и ручной retry
# =====================================================================

@router.get("/outbox", response_model=List[EventOutboxResponse])
async def list_outbox(
    request: Request,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    safe_limit = max(1, min(int(limit or 100), 500))
    q = select(EventOutbox).order_by(EventOutbox.created_at.desc()).limit(safe_limit)
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if statuses:
            q = q.where(EventOutbox.status.in_(statuses))
    if event_type:
        q = q.where(EventOutbox.event_type == event_type)
    if entity_type:
        q = q.where(EventOutbox.entity_type == entity_type)
    if entity_id:
        q = q.where(EventOutbox.entity_id == str(entity_id))
    rows = (await db.execute(q)).scalars().all()
    return [serialize_outbox_row(r) for r in rows]


@router.get("/outbox/{row_id}", response_model=EventOutboxResponse)
async def get_outbox_row(
    row_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    row = (await db.execute(select(EventOutbox).where(EventOutbox.id == row_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Outbox row not found")
    return serialize_outbox_row(row)


@router.post("/outbox/{row_id}/retry", response_model=EventOutboxResponse)
async def retry_outbox_row(
    row_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Сбросить строку обратно в pending (для DLQ или failed).
    Воркер подхватит её на следующем тике."""
    _require_superuser(request)
    row = (await db.execute(select(EventOutbox).where(EventOutbox.id == row_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Outbox row not found")
    if row.status == "delivered":
        raise HTTPException(status_code=400, detail="Already delivered")
    await db.execute(
        update(EventOutbox)
        .where(EventOutbox.id == row_id)
        .values(
            status="pending",
            attempt_count=0,
            scheduled_at=datetime.now(),
            last_error=None,
        )
    )
    await db.commit()
    row = (await db.execute(select(EventOutbox).where(EventOutbox.id == row_id))).scalar_one_or_none()
    return serialize_outbox_row(row)


# =====================================================================
# Subscriptions: CRUD
# =====================================================================

@router.get("/subscriptions", response_model=List[EventSubscriptionResponse])
async def list_subscriptions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    rows = (await db.execute(
        select(EventSubscription).order_by(EventSubscription.created_at.desc())
    )).scalars().all()
    return rows


@router.post("/subscriptions", response_model=EventSubscriptionResponse)
async def create_subscription(
    payload: EventSubscriptionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    sub = await EventSubscription.create(db, **payload.dict())
    return sub


@router.put("/subscriptions/{sub_id}", response_model=EventSubscriptionResponse)
async def update_subscription(
    sub_id: str,
    payload: EventSubscriptionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    sub = (await db.execute(select(EventSubscription).where(EventSubscription.id == sub_id))).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if data:
        await db.execute(update(EventSubscription).where(EventSubscription.id == sub_id).values(**data))
        await db.commit()
    sub = (await db.execute(select(EventSubscription).where(EventSubscription.id == sub_id))).scalar_one_or_none()
    return sub


@router.delete("/subscriptions/{sub_id}")
async def delete_subscription(
    sub_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_superuser(request)
    sub = (await db.execute(select(EventSubscription).where(EventSubscription.id == sub_id))).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.delete(sub)
    await db.commit()
    return {"ok": True}


# =====================================================================
# Observability: агрегированная статистика для admin-страницы
# =====================================================================

@router.get("/stats")
async def event_bus_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Сводка для observability admin-страницы.

    Возвращает:
      • counts: словарь "статус → кол-во строк" в outbox
      • top_event_types: 10 самых частых event_type за всё время
      • subscriptions: список подписок с per-subscription статистикой
        (deliveries — сколько событий доставлено через dedup-таблицу,
         last_event_id — последнее доставленное событие)
      • totals: общие числа (outbox, dedup, subscriptions)

    Только суперюзер. Числа считаются «как есть» — без кэширования,
    для текущих объёмов это норм (десятки тысяч строк за всё время).
    """
    from sqlalchemy import func as _f
    _require_superuser(request)

    # 1) counts по статусам
    rows = (await db.execute(
        select(EventOutbox.status, _f.count(EventOutbox.id))
        .group_by(EventOutbox.status)
    )).all()
    counts = {row[0]: int(row[1]) for row in rows}
    # Гарантируем что все ключевые статусы есть в ответе (даже с 0).
    for s in ("pending", "delivered", "failed", "dlq"):
        counts.setdefault(s, 0)

    # 2) топ event_type-ов
    top_types_rows = (await db.execute(
        select(EventOutbox.event_type, _f.count(EventOutbox.id).label("c"))
        .group_by(EventOutbox.event_type)
        .order_by(_f.count(EventOutbox.id).desc())
        .limit(10)
    )).all()
    top_event_types = [{"event_type": r[0], "count": int(r[1])} for r in top_types_rows]

    # 3) per-subscription статистика
    subs = (await db.execute(
        select(EventSubscription).order_by(EventSubscription.created_at.desc())
    )).scalars().all()
    sub_stats = []
    for sub in subs:
        # Сколько раз dedup зафиксировал успешную доставку этой подписке.
        delivered_count = (await db.execute(
            select(_f.count(EventDeliveryDedup.event_id))
            .where(EventDeliveryDedup.subscription_id == str(sub.id))
        )).scalar() or 0
        # Последнее событие — для UI "когда что-то приходило".
        last_delivered = (await db.execute(
            select(EventDeliveryDedup.event_id, EventDeliveryDedup.delivered_at)
            .where(EventDeliveryDedup.subscription_id == str(sub.id))
            .order_by(EventDeliveryDedup.delivered_at.desc())
            .limit(1)
        )).first()
        sub_stats.append({
            "id": str(sub.id),
            "name": sub.name,
            "event_type_pattern": sub.event_type_pattern,
            "is_active": bool(sub.is_active),
            "delivered_count": int(delivered_count),
            "last_event_id": last_delivered[0] if last_delivered else None,
            "last_delivered_at": last_delivered[1].isoformat() if last_delivered and last_delivered[1] else None,
        })

    # 4) totals — суммарные числа.
    total_outbox = sum(counts.values())
    total_dedup = (await db.execute(select(_f.count(EventDeliveryDedup.event_id)))).scalar() or 0
    total_subs = len(subs)

    return {
        "counts": counts,
        "top_event_types": top_event_types,
        "subscriptions": sub_stats,
        "totals": {
            "outbox": total_outbox,
            "dedup": int(total_dedup),
            "subscriptions": total_subs,
        },
    }


# =====================================================================
# Test sink: синтетический webhook-приёмник для smoke-проверки воркера.
# Без auth и CSRF (см. main.py open_paths + config CSRF_EXEMPT_PATHS).
# Записывает события в файл backend/logs/event_test_sink.jsonl.
# =====================================================================

import os as _os
_TEST_SINK_LOG = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "logs", "event_test_sink.jsonl")


# ───────────────────────────────────────────────────────────────────
# Simulate (DRY-RUN)
# ───────────────────────────────────────────────────────────────────

@router.post("/simulate")
async def simulate_event(
    request: Request,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """DRY-RUN прогон события: что произойдёт, если этот event эмитнётся.

    Полезно для:
      • отладки condition_json у подписок (видишь сразу что сматчилось);
      • документации интеграторам («вот payload — вот кто его получит»);
      • smoke-теста после деплоя новых @on-хендлеров;
      • поддержки команд («у меня не приходит» → разработчик прогоняет simulate и видит точку отказа).

    Не пишет в outbox, не отправляет webhook'и, не мутирует payload.

    Тело запроса:
        {
          "event_key": "contract.before_status_change",
          "entity_type": "contract",
          "entity_id": "test-123",
          "payload": { "status_after": "completed", ... }
        }

    Ответ — см. финальную структуру в return ниже.
    """
    _require_superuser(request)

    event_key = (body.get("event_key") or "").strip()
    if not event_key:
        raise HTTPException(status_code=400, detail="event_key required")
    entity_type = (body.get("entity_type") or "").strip() or _entity_type_from_key(event_key)
    entity_id = body.get("entity_id") or "__simulate__"
    payload = body.get("payload") or {}
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be an object")

    # Импорты локальные — диспетчер тяжёлый, не хотим грузить при каждом
    # импорте модуля.
    from app.services.event_dispatcher import (
        EventContext,
        dispatch_before_simulate,
        list_handlers,
    )
    from app.services.event_outbox import simulate_subscription_match

    phase = "before" if ".before_" in event_key else (
        "batch" if ".batch_" in event_key else "after"
    )

    ctx = EventContext(
        event_key=event_key,
        entity_type=entity_type,
        entity_id=str(entity_id),
        payload=dict(payload),
        user_id=str(getattr(user, "id", "")) or None,
        source="simulate",
    )

    response: dict = {
        "event_key": event_key,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "phase": phase,
        "input_payload": payload,
    }

    if phase == "before":
        # Прогоняем dry-run before-фазы.
        before_report = await dispatch_before_simulate(event_key, ctx)
        response["before"] = before_report
        # Outbox/subscriptions не релевантны для before-фазы — она НЕ
        # пишет в outbox. Возвращаем явно пустой список для ясности.
        response["would_emit_outbox"] = False
        response["subscriptions"] = {
            "matched": [],
            "skipped": [],
            "note": "before-фаза не пишет в outbox; subscriptions матчатся только для after_/batch_",
        }
        # Если фаза была бы отменена — финальное состояние «не дошло».
        if not before_report.get("would_proceed"):
            response["status"] = "would_cancel"
        else:
            response["status"] = "would_proceed_to_business_action"
    else:
        # after/batch — в реальности шёл бы emit_event → outbox → worker.
        # Симулируем match подписок на эту payload.
        sub_report = await simulate_subscription_match(db, event_key, payload)
        # А ещё показать какие @on(after_*) сработают — у них тоже
        # могут быть side effects, важно увидеть.
        all_handlers = list_handlers().get(event_key, [])
        after_handlers = [h for h in all_handlers if h.get("phase") == "after"]
        response["after"] = {
            "in_process_handlers": after_handlers,
            "note": "in-process after-handlers не симулируем (могут иметь side effects); показан список",
        }
        response["would_emit_outbox"] = True
        response["subscriptions"] = sub_report
        response["status"] = "would_emit"

    return response


def _entity_type_from_key(event_key: str) -> str:
    """contract.after_create → contract; '' → ''."""
    if "." in event_key:
        return event_key.split(".", 1)[0]
    return ""


@router.post("/_test/webhook-sink")
async def test_sink(
    request: Request,
    body: dict = Body(...),
    x_event_id: Optional[str] = Header(None),
    x_event_type: Optional[str] = Header(None),
    x_event_signature: Optional[str] = Header(None),
    x_subscription_id: Optional[str] = Header(None),
):
    """Тестовый приёмник. Логирует входящее событие в jsonl-файл и
    возвращает 200. Используется для smoke-проверки воркера."""
    try:
        _os.makedirs(_os.path.dirname(_TEST_SINK_LOG), exist_ok=True)
        record = {
            "received_at": datetime.now().isoformat(),
            "event_id": x_event_id,
            "event_type": x_event_type,
            "subscription_id": x_subscription_id,
            "signature": x_event_signature,
            "body": body,
        }
        with open(_TEST_SINK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        logger.exception("test_sink log write failed: %s", exc)
    return {"received": True, "event_id": x_event_id}


@router.get("/_test/webhook-sink/log")
async def test_sink_log(
    request: Request,
    user: User = Depends(CurrentUser),
):
    """Вернуть последние строки лога test-sink для UI проверки."""
    _require_superuser(request)
    if not _os.path.exists(_TEST_SINK_LOG):
        return []
    try:
        with open(_TEST_SINK_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
        return [json.loads(ln) for ln in lines if ln.strip()]
    except Exception as exc:
        logger.exception("test_sink_log read failed: %s", exc)
        return []
