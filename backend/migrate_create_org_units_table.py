#!/usr/bin/env python3
"""
Create `org_units` table (organisation structure tree).

Idempotent — safe to re-run / picked up by migrate_all on startup.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def table_exists(conn, table: str) -> bool:
    try:
        res = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
        ), {"t": table})
        if res.first() is not None:
            return True
    except Exception:
        pass
    try:
        res = await conn.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
        ), {"t": table})
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
        if await table_exists(conn, "org_units"):
            print("org_units table already exists - skipping.")
        else:
            try:
                await conn.execute(text(
                    """
                    CREATE TABLE IF NOT EXISTS org_units (
                        id VARCHAR(36) PRIMARY KEY,
                        parent_id VARCHAR(36) NULL,
                        name VARCHAR(255) NOT NULL,
                        kind VARCHAR(32) NULL,
                        head_user_id VARCHAR(36) NULL,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        path VARCHAR(1024) NULL,
                        depth INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                ))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_org_units_parent_id "
                    "ON org_units (parent_id)"
                ))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_org_units_path "
                    "ON org_units (path)"
                ))
                print("Created org_units table.")
            except Exception as e:
                msg = str(e).lower()
                if "already exists" in msg:
                    print("org_units table already exists - skipping.")
                else:
                    raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
