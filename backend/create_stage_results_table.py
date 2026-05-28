#!/usr/bin/env python3
"""
Migration script to create stage_results table
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_stage_results():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='stage_results'
            """))
            table_exists = result.fetchone()

            if not table_exists:
                await session.execute(text("""
                    CREATE TABLE stage_results (
                        id TEXT PRIMARY KEY,
                        stage_id TEXT NOT NULL,
                        subcontractor_card_id TEXT NOT NULL,
                        deal_id TEXT,
                        product_name VARCHAR(255) NOT NULL,
                        version_label VARCHAR(50) NOT NULL,
                        comment TEXT,
                        yandex_path TEXT NOT NULL,
                        public_url TEXT,
                        created_by VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (stage_id) REFERENCES subcontractor_stages (id),
                        FOREIGN KEY (subcontractor_card_id) REFERENCES subcontractor_cards (id),
                        FOREIGN KEY (deal_id) REFERENCES deals (id)
                    )
                """))
                print("Created stage_results table")

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise


async def main():
    await migrate_stage_results()


if __name__ == "__main__":
    asyncio.run(main())
