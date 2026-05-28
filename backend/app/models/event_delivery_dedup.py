"""
EventDeliveryDedup — per-subscription idempotency для event bus worker'а.

ЗАЧЕМ.  Outbox-строка может иметь несколько подписчиков (event_type=`*`
матчит сразу N webhook'ов). Текущий worker (см. event_outbox_worker.py)
помечает строку `delivered` только когда все подписчики ответили 2xx.
Если последний из них отвалился — строка идёт в `failed`, и при retry
worker заново шлёт POST уже доставленным подписчикам → **дубль** на
их стороне.

Эта таблица фиксирует факт успешной доставки конкретной пары
`(subscription_id, event_id)`. Перед отправкой POST worker сверяется —
если запись уже есть, шаг пропускается.

ТАБЛИЦА.
  PK: (subscription_id, event_id) — natural composite key. Не нужен ни
  суррогатный id, ни sequence: insert идёт через `INSERT OR IGNORE`
  чтобы конкурирующие воркеры (если когда-нибудь будем масштабировать
  горизонтально) не падали с UNIQUE-конфликтом.
  delivered_at — для аудита и потенциального GC старых записей.

GC.  Сейчас GC нет — записей будет ~ кол-во подписчиков × кол-во событий
за всё время. На целевых объёмах (десятки тысяч событий в год) это
~единицы МБ. Когда станет много — добавим джобу удаления записей
`delivered_at < now - 30 days` где `event_id` уже в delivered/dlq
outbox-строках.
"""
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func

from app.database.base import Base


class EventDeliveryDedup(Base):
    __tablename__ = "event_delivery_dedup"

    # Композитный PK: пара «подписка × событие» — гарантия идемпотентности.
    subscription_id = Column(String(36), primary_key=True, nullable=False)
    event_id = Column(String(36), primary_key=True, nullable=False)

    # Когда зафиксировали успешную доставку (UTC сервера БД).
    delivered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Доп. индекс по event_id для быстрого «сколько подписчиков уже
        # получило это событие» (используется в observability).
        Index("ix_event_delivery_dedup_event_id", "event_id"),
        # И по delivered_at — для будущего GC.
        Index("ix_event_delivery_dedup_delivered_at", "delivered_at"),
    )

    @classmethod
    async def mark_delivered(cls, db, subscription_id: str, event_id: str) -> None:
        """Записать факт успешной доставки. Идемпотентно: если уже было —
        no-op (INSERT OR IGNORE на стороне SQLite). Не коммитит — caller
        делает commit в нужный момент.
        """
        from sqlalchemy import insert
        # SQLite-специфичный `OR IGNORE` нужен чтобы при гонке между
        # worker'ами не падать на UNIQUE constraint. Для Postgres
        # эквивалент — `ON CONFLICT DO NOTHING`, но мы пока на SQLite.
        stmt = insert(cls).values(
            subscription_id=str(subscription_id),
            event_id=str(event_id),
            delivered_at=datetime.now(),
        ).prefix_with("OR IGNORE")
        await db.execute(stmt)

    @classmethod
    async def is_delivered(cls, db, subscription_id: str, event_id: str) -> bool:
        """Уже отправляли этой подписке это событие?"""
        from sqlalchemy import select
        row = (await db.execute(
            select(cls.subscription_id).where(
                cls.subscription_id == str(subscription_id),
                cls.event_id == str(event_id),
            ).limit(1)
        )).scalar_one_or_none()
        return row is not None
