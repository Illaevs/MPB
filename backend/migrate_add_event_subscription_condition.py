#!/usr/bin/env python3
"""
Добавляет колонку `condition_json` (JSON nullable) в таблицу
`event_subscriptions`. Используется JSON-Logic-фильтром в worker'е для
сужения доставок: подписка получит событие, только если правило
сматчилось с payload.

Идемпотентно: безопасно запускать повторно.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_column(conn, table_name: str, column_name: str) -> bool:
    cols = inspect(conn).get_columns(table_name)
    return any(c.get("name") == column_name for c in cols)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if not inspect(conn).has_table("event_subscriptions"):
            actions.append("event_subscriptions table missing — run base event_bus migration first")
            print("\n".join(actions))
            return
        if has_column(conn, "event_subscriptions", "condition_json"):
            actions.append("event_subscriptions.condition_json already exists")
        else:
            # SQLite не поддерживает нативный JSON, но JSON хранится как TEXT.
            conn.execute(text("ALTER TABLE event_subscriptions ADD COLUMN condition_json JSON"))
            actions.append("event_subscriptions.condition_json added")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
