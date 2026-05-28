#!/usr/bin/env python3
"""
Migration script to create notifications table.
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


async def migrate_notifications():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "notifications"):
                await session.execute(text("""
                    CREATE TABLE notifications (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        type TEXT DEFAULT 'info',
                        title TEXT NOT NULL,
                        message TEXT,
                        entity_type TEXT,
                        entity_id TEXT,
                        action_url TEXT,
                        is_read BOOLEAN DEFAULT 0,
                        read_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """))
                print("Created notifications table")

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user
                ON notifications(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_read
                ON notifications(is_read)
            """))
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_notifications()


if __name__ == "__main__":
    asyncio.run(main())
