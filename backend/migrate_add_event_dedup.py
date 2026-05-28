#!/usr/bin/env python3
"""
Создаёт таблицу `event_delivery_dedup` для per-subscription идемпотентности
event-bus worker'а (V1.5).

Без этой таблицы при failed-retry outbox-строки worker повторно шлёт POST
тем подписчикам, что уже успешно ответили 2xx → дубль на их стороне.

Idempotent: пропускает таблицу если она уже создана.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "event_delivery_dedup"):
            actions.append("event_delivery_dedup already exists")
        else:
            # Композитный PK (subscription_id, event_id) — естественный
            # natural key, без суррогатного id.
            conn.execute(text(
                """
                CREATE TABLE event_delivery_dedup (
                    subscription_id VARCHAR(36) NOT NULL,
                    event_id VARCHAR(36) NOT NULL,
                    delivered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (subscription_id, event_id)
                )
                """
            ))
            # Доп. индекс по event_id — для observability запросов вроде
            # «сколько подписчиков уже получило это событие».
            conn.execute(text(
                "CREATE INDEX ix_event_delivery_dedup_event_id ON event_delivery_dedup(event_id)"
            ))
            # И по delivered_at — для будущего GC старых записей.
            conn.execute(text(
                "CREATE INDEX ix_event_delivery_dedup_delivered_at ON event_delivery_dedup(delivered_at)"
            ))
            actions.append("event_delivery_dedup created")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
