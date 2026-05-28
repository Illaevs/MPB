#!/usr/bin/env python3
"""
Migration script to update treasury_transactions table.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_treasury_transactions():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='treasury_transactions'
            """))
            table_exists = result.fetchone()

            if not table_exists:
                await session.execute(text("""
                    CREATE TABLE treasury_transactions (
                        id TEXT PRIMARY KEY,
                        doc_num TEXT NOT NULL,
                        transaction_date DATE NOT NULL,
                        amount REAL NOT NULL,
                        calc_type TEXT DEFAULT 'vtb',
                        payer_inn TEXT,
                        payee_inn TEXT,
                        purpose TEXT,
                        remainder REAL DEFAULT 0.0,
                        processed TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                await session.commit()
                print("Created treasury_transactions table")
                return

            result = await session.execute(text("PRAGMA table_info(treasury_transactions)"))
            columns = {row[1] for row in result.fetchall()}

            if "calc_type" not in columns:
                await session.execute(text("ALTER TABLE treasury_transactions ADD COLUMN calc_type TEXT DEFAULT 'vtb'"))
                await session.commit()
                print("Added calc_type column")
            else:
                print("calc_type column already exists")
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_treasury_transactions()


if __name__ == "__main__":
    asyncio.run(main())
