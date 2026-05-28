#!/usr/bin/env python3
"""
Adds companies.work_directions (JSON), companies.rating (FLOAT),
companies.note (TEXT) — направление работ / рейтинг / примечание
для раздела «Контрагенты».

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.core.config import settings  # noqa: F401  (marks this script
# env-aware so migrate_all.discover() auto-runs it under AUTO_MIGRATE;
# engine_sync already targets settings.SQLALCHEMY_DATABASE_URI)
from app.database.session import engine_sync

_ = settings.SQLALCHEMY_DATABASE_URI


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def has_column(conn, table_name: str, column_name: str) -> bool:
    if not has_table(conn, table_name):
        return False
    columns = inspect(conn).get_columns(table_name)
    return any(col.get("name") == column_name for col in columns)


def migrate() -> None:
    actions = []
    specs = [
        ("work_directions", "ALTER TABLE companies ADD COLUMN work_directions JSON"),
        ("rating", "ALTER TABLE companies ADD COLUMN rating FLOAT DEFAULT 0"),
        ("note", "ALTER TABLE companies ADD COLUMN note TEXT"),
    ]
    with engine_sync.begin() as conn:
        if not has_table(conn, "companies"):
            print("companies table not found — nothing to do")
            return
        for column, ddl in specs:
            if has_column(conn, "companies", column):
                actions.append(f"companies.{column} already exists")
            else:
                conn.execute(text(ddl))
                actions.append(f"companies.{column} added")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
