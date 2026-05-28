#!/usr/bin/env python3
"""
Migration script to add contract linkage and de-facto execution tables.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def _table_exists(session, table_name: str) -> bool:
    result = await session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    )
    return result.fetchone() is not None


async def _column_exists(session, table_name: str, column_name: str) -> bool:
    result = await session.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result.fetchall())


async def migrate():
    async with async_session() as session:
        try:
            if await _table_exists(session, "subcontractor_stages"):
                if not await _column_exists(session, "subcontractor_stages", "contract_id"):
                    await session.execute(
                        text("ALTER TABLE subcontractor_stages ADD COLUMN contract_id TEXT")
                    )
                    print("Added contract_id to subcontractor_stages")

            if await _table_exists(session, "subcontractor_products"):
                if not await _column_exists(session, "subcontractor_products", "contract_id"):
                    await session.execute(
                        text("ALTER TABLE subcontractor_products ADD COLUMN contract_id TEXT")
                    )
                    print("Added contract_id to subcontractor_products")

            if not await _table_exists(session, "stage_product_assignments"):
                await session.execute(text("""
                    CREATE TABLE stage_product_assignments (
                        id TEXT PRIMARY KEY,
                        deal_id TEXT NOT NULL,
                        stage_id TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        subcontractor_card_id TEXT NOT NULL,
                        subcontractor_product_id TEXT,
                        contract_id TEXT,
                        due_date DATE,
                        status VARCHAR(50) DEFAULT 'not_started',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (deal_id) REFERENCES deals (id),
                        FOREIGN KEY (stage_id) REFERENCES stages (id),
                        FOREIGN KEY (product_id) REFERENCES products (id),
                        FOREIGN KEY (subcontractor_card_id) REFERENCES subcontractor_cards (id),
                        FOREIGN KEY (subcontractor_product_id) REFERENCES subcontractor_products (id),
                        FOREIGN KEY (contract_id) REFERENCES contracts (id)
                    )
                """))
                print("Created stage_product_assignments table")

            if not await _table_exists(session, "stage_product_subtasks"):
                await session.execute(text("""
                    CREATE TABLE stage_product_subtasks (
                        id TEXT PRIMARY KEY,
                        assignment_id TEXT NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        due_date DATE,
                        status VARCHAR(50) DEFAULT 'not_started',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (assignment_id) REFERENCES stage_product_assignments (id)
                    )
                """))
                print("Created stage_product_subtasks table")

            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
