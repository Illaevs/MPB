"""
EventOutbox — outbox-таблица для надёжной доставки событий внешним
подписчикам.  Каждое бизнес-действие в роутерах вызывает emit_event(),
который пишет строку в эту таблицу В ОДНОЙ ТРАНЗАКЦИИ с бизнес-данными.
Отдельный воркер (scripts/event_outbox_worker.py) дренирует её и
доставляет в HTTP-эндпоинты подписчиков.

Закрывает три ключевых требования из v2-спека event bus:
  - **idempotency**: `event_id` уникальный — повторный emit с тем же id
    игнорируется (no-op);
  - **ordering per entity**: воркер сортирует pending по
    (entity_type, entity_id, created_at);
  - **retry + DLQ**: `attempt_count` инкрементится, `scheduled_at`
    отодвигается по exp-backoff, после порога `status=dlq` и больше не
    дрейнится автоматически.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.sql import func

from app.database.base import Base


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Уникальный идентификатор события — для idempotency на стороне
    # подписчиков (и для дедупа при повторных emit-ах).
    event_id = Column(String(36), nullable=False, unique=True, index=True)

    # Тип события в нотации "<entity>.<action>" (deal.after_create,
    # task.after_status_change, contract.after_create и т.п.).
    event_type = Column(String(64), nullable=False, index=True)

    # Сущность, к которой относится событие — ordering per entity
    # выстраивается по этим двум полям + created_at.
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)

    # Версионируемый payload — внешние подписчики объявляют поддерживаемые
    # версии и payload_version помогает им разруливать миграции.
    payload = Column(JSON, default=dict)
    payload_version = Column(Integer, nullable=False, default=1)

    # V1.5: цепочка причинно-следственной связи — список event_id предков
    # этого события (если оно было сгенерировано в ответ на другое).
    # Пустой массив или NULL = root-событие (родилось из бизнес-операции).
    # Используется для:
    #   • защиты от глубоких циклов (MAX_DEPTH=5 — emit отказывается);
    #   • наглядного дебага в admin-UI «кто родитель»;
    #   • базы для in-process post-handlers Spec v2.
    causation_chain = Column(JSON, default=list)

    # Жизненный цикл строки.
    #   pending     — ждёт обработки воркером
    #   delivering  — воркер сейчас этим занимается (внутренний lock)
    #   delivered   — успешно доставлено всем подписчикам
    #   failed      — последняя попытка упала, ждём следующий backoff
    #   dlq         — превышен лимит попыток, ручной retry через UI
    status = Column(String(16), nullable=False, default="pending", index=True)

    # Сколько попыток уже было (для exp-backoff и DLQ-порога).
    attempt_count = Column(Integer, nullable=False, default=0)
    # Текст последней ошибки (для отладки в UI).
    last_error = Column(Text)

    # Когда событие можно брать в работу (для exp-backoff). По умолчанию
    # сразу. Worker берёт только строки с scheduled_at <= now().
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    # Когда успешно доставлено.
    delivered_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def create(cls, db, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("event_id", str(uuid.uuid4()))
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("attempt_count", 0)
        kwargs.setdefault("payload_version", 1)
        kwargs.setdefault("created_at", datetime.now())
        item = cls(**kwargs)
        db.add(item)
        # NB: commit/flush — на стороне вызывающего кода, чтобы запись
        # outbox шла в той же транзакции что бизнес-данные.
        return item
