#!/usr/bin/env python3
"""
Добавляет колонку `causation_chain` (JSON) в таблицу `event_outbox` для
V1.5 расширения recursion guard.

V1 имел простой contextvar-флаг «сейчас идёт emit — не пускать вложенный».
V1.5 хранит явную цепочку причинности `[parent_event_id, ...]` — это даёт:
  • observability (видно «кто родитель» в UI/логах);
  • защиту от глубоких циклов (MAX_DEPTH=5 — WARN + skip);
  • основу для in-process post-handlers Spec v2 (worker сможет
    выставлять contextvar перед вызовом хендлера).

Idempotent: PRAGMA table_info → ALTER TABLE ADD COLUMN если колонки нет.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_column(conn, table: str, column: str) -> bool:
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if not inspect(conn).has_table("event_outbox"):
            actions.append("event_outbox table missing — run migrate_add_event_bus.py first")
        elif has_column(conn, "event_outbox", "causation_chain"):
            actions.append("event_outbox.causation_chain already exists")
        else:
            # SQLite не валидирует JSON-тип строго, поэтому используем
            # text — Pydantic/SQLAlchemy на стороне ORM воспримет как JSON.
            conn.execute(text(
                "ALTER TABLE event_outbox ADD COLUMN causation_chain TEXT"
            ))
            actions.append("event_outbox.causation_chain added")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
