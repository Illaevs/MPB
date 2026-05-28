#!/usr/bin/env python3
"""
Adds approval_templates.tags column (JSON array of strings) for tagging
templates in the «Конструктор цепочек» admin page.

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, name: str) -> bool:
    return inspect(conn).has_table(name)


def has_column(conn, table: str, column: str) -> bool:
    if not has_table(conn, table):
        return False
    cols = inspect(conn).get_columns(table)
    return any(c.get("name") == column for c in cols)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        dialect = conn.dialect.name
        if has_table(conn, "approval_templates") and not has_column(conn, "approval_templates", "tags"):
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE approval_templates ADD COLUMN tags JSONB DEFAULT '[]'::jsonb"))
            else:
                conn.execute(text("ALTER TABLE approval_templates ADD COLUMN tags JSON"))
                conn.execute(text("UPDATE approval_templates SET tags = '[]' WHERE tags IS NULL"))
            actions.append("approval_templates.tags added")
        else:
            actions.append("approval_templates.tags already exists or table missing")
    print("\n".join(actions))


if __name__ == "__main__":
    migrate()
