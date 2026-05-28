#!/usr/bin/env python3
"""
Adds companies.contacts column (JSON list of {name, position, phone, email})
for the structured contact persons list in the Companies form.

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
        if has_table(conn, "companies") and not has_column(conn, "companies", "contacts"):
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE companies ADD COLUMN contacts JSONB DEFAULT '[]'::jsonb"))
            else:
                conn.execute(text("ALTER TABLE companies ADD COLUMN contacts JSON"))
                conn.execute(text("UPDATE companies SET contacts = '[]' WHERE contacts IS NULL"))
            actions.append("companies.contacts added")
        else:
            actions.append("companies.contacts already exists or table missing")
    print("\n".join(actions))


if __name__ == "__main__":
    migrate()
