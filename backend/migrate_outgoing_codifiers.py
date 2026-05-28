#!/usr/bin/env python3
"""
Add recipient codifier fields to outgoing_documents table.
Works for SQLite and Postgres.
"""
from app.core.config import settings
from app.database.session import engine_sync
from sqlalchemy import text


def _is_sqlite() -> bool:
    return settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite://")


def _column_exists(conn, table: str, column: str) -> bool:
    if _is_sqlite():
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return any(row[1] == column for row in result.fetchall())
    result = conn.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
              AND column_name = :column_name
        """
        ),
        {"table_name": table, "column_name": column},
    )
    return result.first() is not None


def main() -> None:
    columns = {
        "recipient_short_name": "VARCHAR(255)",
        "recipient_to_name": "VARCHAR(255)",
        "recipient_appeal": "VARCHAR(255)",
        "recipient_eio": "VARCHAR(255)",
        "recipient_salutation": "VARCHAR(32)",
    }

    with engine_sync.begin() as conn:
        for name, sql_type in columns.items():
            if _column_exists(conn, "outgoing_documents", name):
                continue
            conn.execute(text(f"ALTER TABLE outgoing_documents ADD COLUMN {name} {sql_type}"))
            print(f"Added column {name}")


if __name__ == "__main__":
    main()
