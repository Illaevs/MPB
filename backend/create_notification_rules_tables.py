#!/usr/bin/env python3
"""
Migration script to create notification rules/preferences/subscriptions tables
and extend notifications table columns when missing.
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


async def _column_exists(session, table_name: str, column_name: str) -> bool:
    result = await session.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


async def _add_column(session, table: str, column_sql: str):
    await session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))


async def migrate():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "notification_rules"):
                await session.execute(text("""
                    CREATE TABLE notification_rules (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        trigger TEXT NOT NULL,
                        entity_type TEXT,
                        priority TEXT DEFAULT 'info',
                        audience_type TEXT DEFAULT 'assigned_user',
                        audience_value TEXT,
                        require_subscription BOOLEAN DEFAULT 0,
                        conditions TEXT,
                        quiet_policy TEXT DEFAULT 'respect',
                        deliver_in_app BOOLEAN DEFAULT 1,
                        throttle_minutes INTEGER DEFAULT 0,
                        title_template TEXT,
                        message_template TEXT,
                        action_url_template TEXT,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
            if not await _table_exists(session, "notification_subscriptions"):
                await session.execute(text("""
                    CREATE TABLE notification_subscriptions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        is_muted BOOLEAN DEFAULT 0,
                        mute_until TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, entity_type, entity_id)
                    )
                """))
            if not await _table_exists(session, "notification_preferences"):
                await session.execute(text("""
                    CREATE TABLE notification_preferences (
                        user_id TEXT PRIMARY KEY,
                        timezone TEXT DEFAULT 'Europe/Moscow',
                        quiet_hours_start TEXT DEFAULT '22:00',
                        quiet_hours_end TEXT DEFAULT '08:00',
                        digest_enabled BOOLEAN DEFAULT 1,
                        digest_time TEXT DEFAULT '09:00',
                        deliver_in_app BOOLEAN DEFAULT 1,
                        digest_last_sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
            if not await _table_exists(session, "notification_jobs"):
                await session.execute(text("""
                    CREATE TABLE notification_jobs (
                        name TEXT PRIMARY KEY,
                        last_run_at TIMESTAMP
                    )
                """))

            if await _table_exists(session, "notifications"):
                columns = [
                    ("priority", "priority TEXT DEFAULT 'info'"),
                    ("rule_id", "rule_id TEXT"),
                    ("source_event_id", "source_event_id TEXT"),
                    ("deliver_at", "deliver_at TIMESTAMP"),
                ]
                for name, ddl in columns:
                    if not await _column_exists(session, "notifications", name):
                        await _add_column(session, "notifications", ddl)

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notification_rules_trigger
                ON notification_rules(trigger)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_user
                ON notification_subscriptions(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_rule
                ON notifications(rule_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_source
                ON notifications(source_event_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notifications_deliver_at
                ON notifications(deliver_at)
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
