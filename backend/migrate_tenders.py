#!/usr/bin/env python3
"""
Migration script to create tender and accreditation tables.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_tenders():
    async with async_session() as session:
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS tenders (
                    id TEXT PRIMARY KEY,
                    deal_product_id TEXT NOT NULL,
                    deal_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    direction_id TEXT,
                    status TEXT DEFAULT 'new',
                    winner_company_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (deal_product_id) REFERENCES deal_products (id),
                    FOREIGN KEY (deal_id) REFERENCES deals (id),
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (winner_company_id) REFERENCES companies (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS tender_offers (
                    id TEXT PRIMARY KEY,
                    tender_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    status TEXT DEFAULT 'invited',
                    proposed_amount REAL,
                    proposed_deadline DATE,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (tender_id) REFERENCES tenders (id),
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS company_accreditations (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    direction_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS company_documents (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    doc_value TEXT,
                    file_name TEXT,
                    file_url TEXT,
                    status TEXT DEFAULT 'pending',
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tenders_deal_product
                ON tenders(deal_product_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tender_offers_tender
                ON tender_offers(tender_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tender_offers_company
                ON tender_offers(company_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_accreditations_company
                ON company_accreditations(company_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_accreditations_direction
                ON company_accreditations(direction_id)
            """))

            await session.commit()
            print("Tender tables migrated")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_tenders()


if __name__ == "__main__":
    asyncio.run(main())
