#!/usr/bin/env python3
"""
Add `edit_all` and `edit_assigned` boolean columns to `role_permissions`.

Conservative migration: new columns default to 0 (False). Existing
read_all / read_assigned values are NOT touched, so current roles keep
their read scope and simply lose write until an admin re-grants edit.

Idempotent — safe to re-run.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def column_exists(conn, table: str, column: str) -> bool:
    """Try SQLite PRAGMA, then Postgres information_schema. Never raises."""
    try:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        rows = res.fetchall()
        if rows:
            return any(row[1] == column for row in rows)
    except Exception:
        pass
    try:
        res = await conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ), {"t": table, "c": column})
        return res.first() is not None
    except Exception:
        return False


async def add_bool_column(conn, table: str, column: str):
    if await column_exists(conn, table, column):
        print(f"{table}.{column} already exists — skipping ALTER.")
        return
    try:
        await conn.execute(text(
            f"ALTER TABLE {table} ADD COLUMN {column} BOOLEAN NOT NULL DEFAULT 0"
        ))
        print(f"Added {table}.{column} column.")
    except Exception as e:
        msg = str(e).lower()
        if "duplicate column" in msg or "already exists" in msg:
            print(f"{table}.{column} already exists — skipping ALTER.")
        else:
            raise


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace(
        "sqlite:///", "sqlite+aiosqlite:///"
    )
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        await add_bool_column(conn, "role_permissions", "edit_all")
        await add_bool_column(conn, "role_permissions", "edit_assigned")
        # Normalize any NULLs (e.g. if a prior partial run left them) to 0.
        try:
            await conn.execute(text(
                "UPDATE role_permissions SET edit_all = 0 WHERE edit_all IS NULL"
            ))
            await conn.execute(text(
                "UPDATE role_permissions SET edit_assigned = 0 "
                "WHERE edit_assigned IS NULL"
            ))
        except Exception as e:
            print(f"NULL normalization skipped (non-fatal): {e}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
