#!/usr/bin/env python3
"""
Add nullable `submission_deadline` column to `tenders`.

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
        if await column_exists(conn, "tenders", "submission_deadline"):
            print("tenders.submission_deadline already exists - skipping.")
        else:
            try:
                await conn.execute(text(
                    "ALTER TABLE tenders ADD COLUMN submission_deadline TIMESTAMP"
                ))
                print("Added tenders.submission_deadline column.")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print("tenders.submission_deadline already exists - skipping.")
                else:
                    raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
