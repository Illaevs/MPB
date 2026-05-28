#!/usr/bin/env python3
"""
Adds tasks.due_time column ('HH:MM' string) for optional time-of-day on tasks
shown in the calendar day/week timeline view.

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def has_column(conn, table_name: str, column_name: str) -> bool:
    if not has_table(conn, table_name):
        return False
    columns = inspect(conn).get_columns(table_name)
    return any(col.get("name") == column_name for col in columns)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "tasks") and not has_column(conn, "tasks", "due_time"):
            conn.execute(text("ALTER TABLE tasks ADD COLUMN due_time VARCHAR(5)"))
            actions.append("tasks.due_time added")
        else:
            actions.append("tasks.due_time already exists")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
