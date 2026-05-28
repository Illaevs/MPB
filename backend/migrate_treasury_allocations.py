#!/usr/bin/env python3
"""
Migration script to create treasury_allocations and backfill from income_expense_id.
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_treasury_allocations():
    async with async_session() as session:
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS treasury_allocations (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    income_expense_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES treasury_transactions (id),
                    FOREIGN KEY (income_expense_id) REFERENCES income_expense_entries (id)
                )
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_treasury_allocations_tx
                ON treasury_allocations(transaction_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_treasury_allocations_entry
                ON treasury_allocations(income_expense_id)
            """))

            columns = await session.execute(text("PRAGMA table_info(treasury_transactions)"))
            column_names = {row[1] for row in columns.fetchall()}

            if "income_expense_id" in column_names:
                existing = await session.execute(text("""
                    SELECT transaction_id, income_expense_id FROM treasury_allocations
                """))
                existing_pairs = {(row[0], row[1]) for row in existing.fetchall()}

                rows = await session.execute(text("""
                    SELECT id, income_expense_id, amount, category_code
                    FROM treasury_transactions
                    WHERE income_expense_id IS NOT NULL
                """))
                to_insert = []
                for tx_id, entry_id, amount, category_code in rows.fetchall():
                    if (tx_id, entry_id) in existing_pairs:
                        continue
                    to_insert.append({
                        "id": str(uuid.uuid4()),
                        "transaction_id": tx_id,
                        "income_expense_id": entry_id,
                        "amount": abs(amount),
                        "category_code": category_code,
                    })

                if to_insert:
                    await session.execute(text("""
                        INSERT INTO treasury_allocations (id, transaction_id, income_expense_id, amount, category_code)
                        VALUES (:id, :transaction_id, :income_expense_id, :amount, :category_code)
                    """), to_insert)

            if "remainder" in column_names:
                await session.execute(text("""
                    UPDATE treasury_transactions
                    SET remainder = (
                        SELECT MAX(ABS(t.amount) - COALESCE((
                            SELECT SUM(a.amount) FROM treasury_allocations a
                            WHERE a.transaction_id = t.id
                        ), 0), 0)
                        FROM treasury_transactions t
                        WHERE t.id = treasury_transactions.id
                    )
                """))

            await session.commit()
            print("Treasury allocations migrated")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_treasury_allocations()


if __name__ == "__main__":
    asyncio.run(main())
