#!/usr/bin/env python3
"""
Создаёт таблицы event_outbox и event_subscriptions для прототипа event bus.

Idempotent: при повторном запуске пропускает уже существующие таблицы.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "event_outbox"):
            actions.append("event_outbox already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE event_outbox (
                    id VARCHAR(36) PRIMARY KEY,
                    event_id VARCHAR(36) NOT NULL UNIQUE,
                    event_type VARCHAR(64) NOT NULL,
                    entity_type VARCHAR(64) NOT NULL,
                    entity_id VARCHAR(36) NOT NULL,
                    payload JSON,
                    payload_version INTEGER NOT NULL DEFAULT 1,
                    status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    scheduled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    delivered_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
                """
            ))
            conn.execute(text("CREATE INDEX ix_event_outbox_event_id ON event_outbox(event_id)"))
            conn.execute(text("CREATE INDEX ix_event_outbox_event_type ON event_outbox(event_type)"))
            conn.execute(text("CREATE INDEX ix_event_outbox_entity_type ON event_outbox(entity_type)"))
            conn.execute(text("CREATE INDEX ix_event_outbox_entity_id ON event_outbox(entity_id)"))
            conn.execute(text("CREATE INDEX ix_event_outbox_status ON event_outbox(status)"))
            conn.execute(text("CREATE INDEX ix_event_outbox_created_at ON event_outbox(created_at)"))
            # Композитный индекс под ordering per entity + дренаж по
            # scheduled_at — это горячий путь воркера.
            conn.execute(text(
                "CREATE INDEX ix_event_outbox_drain ON event_outbox(status, scheduled_at, entity_type, entity_id, created_at)"
            ))
            actions.append("event_outbox created")

        if has_table(conn, "event_subscriptions"):
            actions.append("event_subscriptions already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE event_subscriptions (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    event_type_pattern VARCHAR(128) NOT NULL,
                    delivery_method VARCHAR(16) NOT NULL DEFAULT 'webhook',
                    target_url VARCHAR(1024) NOT NULL,
                    hmac_secret VARCHAR(255) NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
                """
            ))
            conn.execute(text(
                "CREATE INDEX ix_event_subscriptions_pattern ON event_subscriptions(event_type_pattern)"
            ))
            actions.append("event_subscriptions created")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
