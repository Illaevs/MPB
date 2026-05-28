#!/usr/bin/env python3
"""
Migration script to add company_id to subcontractor_cards table
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_subcontractor_cards():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                PRAGMA table_info(subcontractor_cards)
            """))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            if "company_id" not in column_names:
                print("Adding company_id column...")
                await session.execute(text("""
                    ALTER TABLE subcontractor_cards ADD COLUMN company_id TEXT
                """))

            await session.commit()
            print("Subcontractor cards migration completed successfully!")
        except Exception as e:
            print(f"Subcontractor cards migration failed: {e}")
            await session.rollback()
            raise


async def main():
    await migrate_subcontractor_cards()


if __name__ == "__main__":
    asyncio.run(main())
