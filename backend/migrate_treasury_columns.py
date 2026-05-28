#!/usr/bin/env python3
"""
Migration script to update treasury_transactions columns.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_columns():
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
                        payer_name TEXT,
                        payee_name TEXT,
                        purpose TEXT,
                        category_code TEXT,
                        ignore_flag TEXT DEFAULT 'Нет',
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
            if "payer_name" not in columns:
                await session.execute(text("ALTER TABLE treasury_transactions ADD COLUMN payer_name TEXT"))
            if "payee_name" not in columns:
                await session.execute(text("ALTER TABLE treasury_transactions ADD COLUMN payee_name TEXT"))
            if "category_code" not in columns:
                await session.execute(text("ALTER TABLE treasury_transactions ADD COLUMN category_code TEXT"))
            if "ignore_flag" not in columns:
                await session.execute(text("ALTER TABLE treasury_transactions ADD COLUMN ignore_flag TEXT DEFAULT 'Нет'"))

            await session.commit()
            print("Treasury columns updated")
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_columns()


if __name__ == "__main__":
    asyncio.run(main())
