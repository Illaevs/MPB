#!/usr/bin/env python3
"""
Add nullable `org_unit_id` column to `users` (link to org_units tree).

Idempotent — safe to re-run / picked up by migrate_all on startup.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def column_exists(conn, table: str, column: str) -> bool:
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


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace(
        "sqlite:///", "sqlite+aiosqlite:///"
    )
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        if await column_exists(conn, "users", "org_unit_id"):
            print("users.org_unit_id already exists - skipping.")
        else:
            try:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN org_unit_id VARCHAR(36)"
                ))
                print("Added users.org_unit_id column.")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print("users.org_unit_id already exists - skipping.")
                else:
                    raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
