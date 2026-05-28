#!/usr/bin/env python3
"""
Migration script to create income_expense_entries table and link treasury transactions.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_income_expense():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='income_expense_entries'
            """))
            table_exists = result.fetchone()

            if not table_exists:
                await session.execute(text("""
                    CREATE TABLE income_expense_entries (
                        id TEXT PRIMARY KEY,
                        direction TEXT NOT NULL,
                        amount REAL NOT NULL,
                        plan_date DATE NOT NULL,
                        actual_date DATE,
                        payer_id TEXT,
                        payee_id TEXT,
                        deal_id TEXT,
                        contract_id TEXT,
                        stage_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (payer_id) REFERENCES companies (id),
                        FOREIGN KEY (payee_id) REFERENCES companies (id),
                        FOREIGN KEY (deal_id) REFERENCES deals (id),
                        FOREIGN KEY (contract_id) REFERENCES contracts (id),
                        FOREIGN KEY (stage_id) REFERENCES stages (id)
                    )
                """))
                print("Created income_expense_entries table")
            else:
                result = await session.execute(text("PRAGMA table_info(income_expense_entries)"))
                entry_columns = {row[1] for row in result.fetchall()}
                missing_columns = {
                    "deal_id": "ALTER TABLE income_expense_entries ADD COLUMN deal_id TEXT",
                    "contract_id": "ALTER TABLE income_expense_entries ADD COLUMN contract_id TEXT",
                    "stage_id": "ALTER TABLE income_expense_entries ADD COLUMN stage_id TEXT",
                }
                for column, ddl in missing_columns.items():
                    if column not in entry_columns:
                        await session.execute(text(ddl))
                        print(f"Added {column} column to income_expense_entries")

            result = await session.execute(text("PRAGMA table_info(treasury_transactions)"))
            columns = {row[1] for row in result.fetchall()}

            if "income_expense_id" not in columns:
                await session.execute(text(
                    "ALTER TABLE treasury_transactions ADD COLUMN income_expense_id TEXT"
                ))
                print("Added income_expense_id column to treasury_transactions")

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_income_expense()


if __name__ == "__main__":
    asyncio.run(main())
