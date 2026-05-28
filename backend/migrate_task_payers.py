#!/usr/bin/env python3
"""
Migration script to add payer/payee columns to tasks.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_task_payers():
    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE tasks ADD COLUMN payer_id TEXT
            """))
            await session.execute(text("""
                ALTER TABLE tasks ADD COLUMN payee_id TEXT
            """))
            await session.commit()
            print("Task payer/payee columns migrated")
        except Exception as exc:
            await session.rollback()
            message = str(exc).lower()
            if "duplicate column name" in message or "already exists" in message:
                print("Task payer/payee columns already exist")
                return
            print(f"Task payer/payee migration failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_task_payers())
