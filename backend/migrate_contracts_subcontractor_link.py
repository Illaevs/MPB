#!/usr/bin/env python3
"""
Migration script to add subcontractor_card_id to contracts table
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_contracts_table():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                PRAGMA table_info(contracts)
            """))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            if "subcontractor_card_id" not in column_names:
                print("Adding subcontractor_card_id column...")
                await session.execute(text("""
                    ALTER TABLE contracts ADD COLUMN subcontractor_card_id TEXT
                """))

            await session.commit()
            print("Contracts migration completed successfully!")
        except Exception as e:
            print(f"Contracts migration failed: {e}")
            await session.rollback()
            raise


async def main():
    await migrate_contracts_table()


if __name__ == "__main__":
    asyncio.run(main())
