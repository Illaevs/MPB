#!/usr/bin/env python3
"""
Add the `work_directions` column to `companies`.

The ORM model (app/models/company.py) and schema declare
`work_directions` (JSON list of category ids), but environments seeded
before that column existed are missing it -> every code path that
serializes a company 500s with
`no such column: companies.work_directions` (e.g. outgoing-registry).

Idempotent — safe to re-run. Picked up automatically by migrate_all /
AUTO_MIGRATE (matches `add_*column*.py` and reads SQLALCHEMY_DATABASE_URI).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def column_exists(conn, table: str, column: str) -> bool:
    """SQLite PRAGMA first, then Postgres information_schema. Never raises."""
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
        if await column_exists(conn, "companies", "work_directions"):
            print("companies.work_directions already exists — skipping ALTER.")
        else:
            # JSON keyword: TEXT affinity on SQLite, json on Postgres.
            try:
                await conn.execute(text(
                    "ALTER TABLE companies ADD COLUMN work_directions JSON"
                ))
                print("Added companies.work_directions column.")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print("companies.work_directions already exists — skipping.")
                else:
                    raise

        # Backfill NULL -> '[]' so ORM JSON reads return a list, not None.
        await conn.execute(text(
            "UPDATE companies SET work_directions = '[]' "
            "WHERE work_directions IS NULL"
        ))
        print("Backfilled NULL work_directions to empty list.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
