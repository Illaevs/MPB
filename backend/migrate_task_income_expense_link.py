#!/usr/bin/env python3
"""
Migration script to add income_expense_id column to tasks.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_task_income_expense_link():
    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE tasks ADD COLUMN income_expense_id TEXT
            """))
            await session.commit()
            print("Task income_expense_id column migrated")
        except Exception as exc:
            await session.rollback()
            message = str(exc).lower()
            if "duplicate column name" in message or "already exists" in message:
                print("Task income_expense_id column already exists")
                return
            print(f"Task income_expense_id migration failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_task_income_expense_link())
