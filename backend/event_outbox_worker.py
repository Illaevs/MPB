#!/usr/bin/env python3
"""
Воркер event bus: дренирует event_outbox-таблицу и доставляет события
подписчикам.

Запускается отдельным процессом (как notifications_worker.py).  Не нужно
поднимать вместе с web-сервером — event_outbox copes без него: события
просто накапливаются со статусом pending.  В проде запускается одной
инстанцией (single-writer на каждую entity для ordering); горизонтально
масштабировать можно только аккуратно (с distributed-lock на entity_id).

Архитектура цикла:
  1. SELECT batch pending|failed строк, scheduled_at <= now(),
     ORDER BY entity_type, entity_id, created_at — это даёт нам
     ordering per entity внутри батча.
  2. Для каждой строки находим подписки по event_type_pattern.
  3. Для каждой подписки отправляем HTTP POST с HMAC-подписью.
  4. Если ВСЕ подписки ответили 2xx — status=delivered.  Иначе:
     status=failed, attempt_count++, scheduled_at += exp.backoff.
  5. attempt_count >= MAX_ATTEMPTS → status=dlq, ручной retry через UI.

Расписание поллинга: каждые POLL_INTERVAL_SEC секунд (3 по умолчанию).
Между батчами успешной обработки — небольшая задержка, чтобы не молотить
БД при пустом outbox.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

import httpx
from sqlalchemy import select, update

# Добавляем backend/ в sys.path для запуска из любого места.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import async_session
from app.models import EventOutbox, EventDeliveryDedup
from app.services.event_outbox import list_matching_subscriptions, serialize_outbox_row

logger = logging.getLogger("event_outbox_worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

POLL_INTERVAL_SEC = float(os.getenv("EVENT_OUTBOX_POLL_SEC", "3"))
BATCH_SIZE = int(os.getenv("EVENT_OUTBOX_BATCH", "50"))
MAX_ATTEMPTS = int(os.getenv("EVENT_OUTBOX_MAX_ATTEMPTS", "5"))
HTTP_TIMEOUT_SEC = float(os.getenv("EVENT_OUTBOX_HTTP_TIMEOUT", "10"))


def _backoff_seconds(attempt: int) -> int:
    """Exponential backoff: 0→5s, 1→15s, 2→45s, 3→135s (~2 мин),
    4→405s (~7 мин). После 5-й попытки уходит в DLQ."""
    return min(5 * (3 ** max(0, attempt)), 3600)


def _hmac_sign(secret: str, body: bytes) -> str:
    """HMAC sha256 hex-digest для заголовка X-Event-Signature."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def _fetch_batch(db) -> List[EventOutbox]:
    """Берём pending/failed строки готовые к отправке.
    Ordering per entity: одна сущность обрабатывается строго по
    created_at, разные — параллельно неважно (в рамках одного батча).
    """
    now = datetime.now()
    rows = (await db.execute(
        select(EventOutbox)
        .where(EventOutbox.status.in_(["pending", "failed"]))
        .where(EventOutbox.scheduled_at <= now)
        .order_by(
            EventOutbox.entity_type,
            EventOutbox.entity_id,
            EventOutbox.created_at,
        )
        .limit(BATCH_SIZE)
    )).scalars().all()
    return list(rows)


async def _deliver_one(
    client: httpx.AsyncClient,
    db,
    row: EventOutbox,
    subscriptions: list,
) -> Dict[str, Any]:
    """Пытается доставить one row всем подписчикам с учётом dedup.

    Для каждой подписки сверяется с `event_delivery_dedup` —
    если эта пара (sub_id, event_id) уже доставлена, шаг пропускается.
    После успешного POST — фиксируем в dedup, чтобы при retry
    failed-строки не отправить тем же подписчикам повторно.

    Возвращает {"ok": bool, "error": str|None, "delivered_to": [ids]}.
    `ok=True` если ВСЕ подписчики либо уже были в dedup, либо
    только что ответили 2xx.
    """
    body_dict = serialize_outbox_row(row)
    body = json.dumps(body_dict, ensure_ascii=False, default=str).encode("utf-8")
    delivered: List[str] = []
    last_err = None
    # Ленивый импорт — модуль не нужен если ни у одной подписки нет condition_json.
    from app.services.json_logic import evaluate as _eval_condition
    event_payload = body_dict.get("payload") or {}

    for sub in subscriptions:
        # Пропускаем подписчиков, которым уже доставили это событие
        # (например, при retry failed-строки).
        already = await EventDeliveryDedup.is_delivered(db, str(sub.id), str(row.event_id))
        if already:
            delivered.append(str(sub.id))
            continue

        # JSON-Logic фильтр: если у подписки есть condition_json и она
        # НЕ матчится с payload — пропускаем доставку И НЕ помечаем в
        # dedup (на случай если правило поправят, при следующем emit-е
        # того же типа решение будет переоценено).
        condition = getattr(sub, "condition_json", None)
        if condition:
            try:
                # condition_json в SQLite приходит как TEXT — может быть строкой JSON.
                if isinstance(condition, str):
                    condition = json.loads(condition)
            except Exception:
                condition = None
        if condition and not _eval_condition(condition, event_payload):
            logger.debug(
                "subscription %s skipped by condition_json on event %s",
                sub.id, row.event_id,
            )
            # Считаем «доставлено» с точки зрения этого подписчика —
            # его правило отфильтровало, retry'ить не надо.
            delivered.append(str(sub.id))
            continue
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Event-Id": str(row.event_id),
                "X-Event-Type": row.event_type,
                # Schema-version в отдельном заголовке: подписчик может
                # роутить по версии без парсинга JSON-тела (например,
                # nginx-route или ingress-фильтр). В JSON-payload
                # дублируется как `payload_version`.
                "X-Event-Schema-Version": str(row.payload_version or 1),
                "X-Event-Signature": _hmac_sign(sub.hmac_secret or "", body),
                "X-Subscription-Id": str(sub.id),
            }
            resp = await client.post(
                sub.target_url,
                content=body,
                headers=headers,
                timeout=HTTP_TIMEOUT_SEC,
            )
            if 200 <= resp.status_code < 300:
                # Сразу фиксируем в dedup — это критично делать ДО
                # очередного retry'а, чтобы при падении worker'а после
                # этой строки мы не отправили дубль.
                await EventDeliveryDedup.mark_delivered(db, str(sub.id), str(row.event_id))
                delivered.append(str(sub.id))
            else:
                last_err = f"sub={sub.id} HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning("Delivery failed: %s", last_err)
        except Exception as exc:
            last_err = f"sub={sub.id} exception: {exc}"
            logger.warning("Delivery failed: %s", last_err)

    if len(delivered) == len(subscriptions):
        return {"ok": True, "error": None, "delivered_to": delivered}
    return {"ok": False, "error": last_err or "no delivery", "delivered_to": delivered}


async def _mark_delivered(db, row_id: str) -> None:
    await db.execute(
        update(EventOutbox)
        .where(EventOutbox.id == row_id)
        .values(
            status="delivered",
            delivered_at=datetime.now(),
            last_error=None,
        )
    )


async def _mark_failed(db, row_id: str, attempt: int, error: str) -> None:
    next_attempt = attempt + 1
    if next_attempt >= MAX_ATTEMPTS:
        new_status = "dlq"
        scheduled_at = None
    else:
        new_status = "failed"
        scheduled_at = datetime.now() + timedelta(seconds=_backoff_seconds(next_attempt))
    values = {
        "status": new_status,
        "attempt_count": next_attempt,
        "last_error": (error or "")[:1000],
    }
    if scheduled_at is not None:
        values["scheduled_at"] = scheduled_at
    await db.execute(
        update(EventOutbox).where(EventOutbox.id == row_id).values(**values)
    )


async def process_batch() -> int:
    """Один проход воркера: возвращает число обработанных строк."""
    async with async_session() as db:
        rows = await _fetch_batch(db)
        if not rows:
            return 0
        logger.info("Draining %d events", len(rows))
        async with httpx.AsyncClient() as client:
            for row in rows:
                subs = await list_matching_subscriptions(db, row.event_type)
                if not subs:
                    # Нет подписчиков — событие считаем сразу доставленным,
                    # чтобы оно не висело в pending бесконечно. Сама строка
                    # остаётся для аудита/последующих ретраев.
                    await _mark_delivered(db, row.id)
                    continue
                result = await _deliver_one(client, db, row, subs)
                if result["ok"]:
                    await _mark_delivered(db, row.id)
                else:
                    await _mark_failed(db, row.id, row.attempt_count, result["error"] or "")
        await db.commit()
        return len(rows)


async def run_loop() -> None:
    logger.info(
        "event_outbox_worker started: poll=%ss batch=%d max_attempts=%d",
        POLL_INTERVAL_SEC, BATCH_SIZE, MAX_ATTEMPTS,
    )
    while True:
        try:
            processed = await process_batch()
            if processed == 0:
                await asyncio.sleep(POLL_INTERVAL_SEC)
            else:
                # При активной нагрузке — короче спим, чтобы быстрее
                # дренировать back-pressure.
                await asyncio.sleep(0.2)
        except Exception as exc:
            logger.exception("worker tick failed: %s", exc)
            await asyncio.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        logger.info("event_outbox_worker stopped")
