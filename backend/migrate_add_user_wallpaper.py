#!/usr/bin/env python3
"""
Adds users.wallpaper_url column for custom per-user shell wallpapers.

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
        if has_table(conn, "users") and not has_column(conn, "users", "wallpaper_url"):
            conn.execute(text("ALTER TABLE users ADD COLUMN wallpaper_url VARCHAR(500)"))
            actions.append("users.wallpaper_url added")
        else:
            actions.append("users.wallpaper_url already exists")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
