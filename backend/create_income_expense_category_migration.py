#!/usr/bin/env python3
"""
Migration script to add category_code to income_expense_entries.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def main():
    async with async_session() as session:
        try:
            result = await session.execute(text("PRAGMA table_info(income_expense_entries)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            if "category_code" not in column_names:
                await session.execute(text("ALTER TABLE income_expense_entries ADD COLUMN category_code VARCHAR(255)"))
            await session.commit()
            print("Income/expense category migration completed successfully!")
        except Exception as exc:
            print(f"Income/expense category migration failed: {exc}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
