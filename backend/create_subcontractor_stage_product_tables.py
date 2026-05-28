#!/usr/bin/env python3
"""
Migration script to create subcontractor stages and products tables
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def _table_exists(session, table_name: str) -> bool:
    result = await session.execute(text("""
        SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


async def migrate_subcontractor_tables():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "subcontractor_stages"):
                await session.execute(text("""
                    CREATE TABLE subcontractor_stages (
                        id TEXT PRIMARY KEY,
                        parent_id TEXT,
                        subcontractor_card_id TEXT NOT NULL,
                        contract_id TEXT,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        stage_type VARCHAR(50) DEFAULT 'stage',
                        term_type VARCHAR(50) DEFAULT 'work_days',
                        date_start DATE NOT NULL,
                        duration INTEGER NOT NULL,
                        date_end DATE,
                        resources JSON,
                        planned_cost FLOAT DEFAULT 0.0,
                        actual_cost FLOAT DEFAULT 0.0,
                        status VARCHAR(50) DEFAULT 'planned',
                        subcontractor_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (subcontractor_card_id) REFERENCES subcontractor_cards (id),
                        FOREIGN KEY (contract_id) REFERENCES contracts (id),
                        FOREIGN KEY (parent_id) REFERENCES subcontractor_stages (id),
                        FOREIGN KEY (subcontractor_id) REFERENCES companies (id)
                    )
                """))
                print("Created subcontractor_stages table")

            if not await _table_exists(session, "subcontractor_stage_dependencies"):
                await session.execute(text("""
                    CREATE TABLE subcontractor_stage_dependencies (
                        id TEXT PRIMARY KEY,
                        predecessor_id TEXT NOT NULL,
                        successor_id TEXT NOT NULL,
                        dependency_type VARCHAR(2) DEFAULT 'FS',
                        lag INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (predecessor_id) REFERENCES subcontractor_stages (id),
                        FOREIGN KEY (successor_id) REFERENCES subcontractor_stages (id)
                    )
                """))
                print("Created subcontractor_stage_dependencies table")

            if not await _table_exists(session, "subcontractor_products"):
                await session.execute(text("""
                    CREATE TABLE subcontractor_products (
                        id TEXT PRIMARY KEY,
                        subcontractor_card_id TEXT NOT NULL,
                        contract_id TEXT,
                        product_id TEXT NOT NULL,
                        custom_name VARCHAR(255),
                        custom_price FLOAT,
                        quantity FLOAT DEFAULT 1.0,
                        unit VARCHAR(50),
                        unit_price FLOAT NOT NULL,
                        discount_percent FLOAT DEFAULT 0.0,
                        discount_amount FLOAT DEFAULT 0.0,
                        tax_rate FLOAT DEFAULT 0.0,
                        currency VARCHAR(3) DEFAULT 'RUB',
                        total_price FLOAT,
                        discount_total FLOAT DEFAULT 0.0,
                        tax_amount FLOAT DEFAULT 0.0,
                        final_price FLOAT,
                        stage_id TEXT,
                        status VARCHAR(50) DEFAULT 'planned',
                        notes TEXT,
                        custom_properties JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (subcontractor_card_id) REFERENCES subcontractor_cards (id),
                        FOREIGN KEY (contract_id) REFERENCES contracts (id),
                        FOREIGN KEY (product_id) REFERENCES products (id),
                        FOREIGN KEY (stage_id) REFERENCES subcontractor_stages (id)
                    )
                """))
                print("Created subcontractor_products table")

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_subcontractor_tables()


if __name__ == "__main__":
    asyncio.run(main())
