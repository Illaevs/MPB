#!/usr/bin/env python3
"""
Migration script to create subcontractor_cards table
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
                SELECT name FROM sqlite_master WHERE type='table' AND name='subcontractor_cards'
            """))
            table_exists = result.fetchone()

            if not table_exists:
                await session.execute(text("""
                    CREATE TABLE subcontractor_cards (
                        id TEXT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        obj_name VARCHAR(500),
                        address TEXT,
                        object_type VARCHAR(100),
                        object_area FLOAT,
                        company_id TEXT,
                        customer_id TEXT,
                        general_contractor_id TEXT,
                        penalty_config JSON,
                        s3_prefix_tz VARCHAR(500),
                        s3_prefix_docs VARCHAR(500),
                        status VARCHAR(50) DEFAULT 'active',
                        total_contract_value FLOAT DEFAULT 0.0,
                        total_paid FLOAT DEFAULT 0.0,
                        vat_rate FLOAT DEFAULT 20.0,
                        vat_included BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id),
                        FOREIGN KEY (customer_id) REFERENCES companies (id),
                        FOREIGN KEY (general_contractor_id) REFERENCES companies (id)
                    )
                """))
                print("Created subcontractor_cards table")

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_subcontractor_cards()


if __name__ == "__main__":
    asyncio.run(main())
