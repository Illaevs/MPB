#!/usr/bin/env python3
"""
Migration script to create contracts table
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def create_contracts_table():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'
            """))
            table_exists = result.fetchone()

            if table_exists:
                print("Contracts table already exists, dropping and recreating...")
                await session.execute(text("DROP TABLE contracts"))

            print("Creating contracts table...")
            await session.execute(text("""
                CREATE TABLE contracts (
                    id TEXT PRIMARY KEY,
                    contract_number TEXT NOT NULL,
                    contract_date DATE NOT NULL,
                    status TEXT DEFAULT 'approval',
                    amount REAL DEFAULT 0.0,
                    contract_type TEXT NOT NULL,
                    customer_id TEXT,
                    executor_id TEXT,
                    deal_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES companies (id),
                    FOREIGN KEY (executor_id) REFERENCES companies (id),
                    FOREIGN KEY (deal_id) REFERENCES deals (id)
                )
            """))
            await session.commit()
            print("Contracts table created successfully!")
        except Exception as e:
            print(f"Contracts table creation failed: {e}")
            await session.rollback()
            raise


async def main():
    print("Starting contracts table creation...")
    await create_contracts_table()
    print("Contracts table creation completed!")


if __name__ == "__main__":
    asyncio.run(main())
