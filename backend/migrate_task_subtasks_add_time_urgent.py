#!/usr/bin/env python3
"""
Adds `due_time` (VARCHAR(5)) and `is_urgent` (BOOLEAN) columns to the
`task_subtasks` table — время дедлайна и флаг «огонёк».

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_column(conn, table_name: str, column_name: str) -> bool:
    cols = inspect(conn).get_columns(table_name)
    return any(c.get("name") == column_name for c in cols)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if not inspect(conn).has_table("task_subtasks"):
            actions.append("task_subtasks table missing — run migrate_add_task_subtasks.py first")
            print("\n".join(actions))
            return
        if has_column(conn, "task_subtasks", "due_time"):
            actions.append("task_subtasks.due_time already exists")
        else:
            conn.execute(text("ALTER TABLE task_subtasks ADD COLUMN due_time VARCHAR(5)"))
            actions.append("task_subtasks.due_time added")
        if has_column(conn, "task_subtasks", "is_urgent"):
            actions.append("task_subtasks.is_urgent already exists")
        else:
            conn.execute(
                text("ALTER TABLE task_subtasks ADD COLUMN is_urgent BOOLEAN NOT NULL DEFAULT 0")
            )
            actions.append("task_subtasks.is_urgent added")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
