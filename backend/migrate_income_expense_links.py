#!/usr/bin/env python3
"""
Migration script to add deal_id and contract_id to income_expense_entries.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_income_expense_links():
    async with async_session() as session:
        try:
            result = await session.execute(text("PRAGMA table_info(income_expense_entries)"))
            columns = {row[1] for row in result.fetchall()}

            if "deal_id" not in columns:
                await session.execute(text("ALTER TABLE income_expense_entries ADD COLUMN deal_id TEXT"))
            if "contract_id" not in columns:
                await session.execute(text("ALTER TABLE income_expense_entries ADD COLUMN contract_id TEXT"))

            await session.commit()
            print("Income/expense link columns updated")
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_income_expense_links()


if __name__ == "__main__":
    asyncio.run(main())
