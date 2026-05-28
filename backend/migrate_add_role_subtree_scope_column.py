#!/usr/bin/env python3
"""
Add `subtree_scope` boolean column to `roles` (default 0 — conservative OFF).

When ON, a user who is the head of an org_unit gets the "own + subtree"
permission scope (Phase 2). Default OFF ⇒ no behaviour change.

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
        if await column_exists(conn, "roles", "subtree_scope"):
            print("roles.subtree_scope already exists - skipping.")
        else:
            try:
                await conn.execute(text(
                    "ALTER TABLE roles ADD COLUMN subtree_scope BOOLEAN "
                    "NOT NULL DEFAULT 0"
                ))
                print("Added roles.subtree_scope column.")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print("roles.subtree_scope already exists - skipping.")
                else:
                    raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
