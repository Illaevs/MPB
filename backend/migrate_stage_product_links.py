#!/usr/bin/env python3
"""
Migration script to add stage_product_links table.
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


async def migrate():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "stage_product_links"):
                await session.execute(text("""
                    CREATE TABLE stage_product_links (
                        id TEXT PRIMARY KEY,
                        deal_id TEXT NOT NULL,
                        stage_id TEXT NOT NULL,
                        deal_product_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (deal_id) REFERENCES deals (id),
                        FOREIGN KEY (stage_id) REFERENCES stages (id),
                        FOREIGN KEY (deal_product_id) REFERENCES deal_products (id)
                    )
                """))
                await session.execute(text("""
                    CREATE UNIQUE INDEX idx_stage_product_links_unique
                    ON stage_product_links(stage_id, deal_product_id)
                """))
                print("Created stage_product_links table")

            # Backfill from deal_products.stage_id if present
            result = await session.execute(
                text("SELECT id, deal_id, stage_id FROM deal_products WHERE stage_id IS NOT NULL")
            )
            rows = result.fetchall()
            for row in rows:
                link_exists = await session.execute(
                    text("""
                        SELECT 1 FROM stage_product_links
                        WHERE stage_id = :stage_id AND deal_product_id = :deal_product_id
                    """),
                    {"stage_id": row[2], "deal_product_id": row[0]},
                )
                if link_exists.fetchone():
                    continue
                await session.execute(
                    text("""
                        INSERT INTO stage_product_links (id, deal_id, stage_id, deal_product_id)
                        VALUES (lower(hex(randomblob(16))), :deal_id, :stage_id, :deal_product_id)
                    """),
                    {"deal_id": row[1], "stage_id": row[2], "deal_product_id": row[0]},
                )
            if rows:
                print("Backfilled stage_product_links from deal_products.stage_id")
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
