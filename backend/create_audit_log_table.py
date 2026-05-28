#!/usr/bin/env python3
"""
Migration script to create audit_logs table.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def _table_exists(session, table_name: str) -> bool:
    result = await session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    )
    return result.fetchone() is not None


async def migrate():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "audit_logs"):
                await session.execute(text("""
                    CREATE TABLE audit_logs (
                        id TEXT PRIMARY KEY,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT,
                        action TEXT NOT NULL,
                        user_id TEXT,
                        source_event_id TEXT,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
                ON audit_logs(entity_type, entity_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user
                ON audit_logs(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_created
                ON audit_logs(created_at)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_source
                ON audit_logs(source_event_id)
            """))
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate()


if __name__ == "__main__":
    asyncio.run(main())
