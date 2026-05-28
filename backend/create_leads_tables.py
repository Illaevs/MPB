#!/usr/bin/env python3
"""
Migration script to create leads and lead_products tables.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def create_leads_table():
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='leads'
        """))
        table_exists = result.fetchone()
        if table_exists:
            print("Leads table already exists")
            await ensure_leads_columns(session)
            return
        print("Creating leads table...")
        await session.execute(text("""
            CREATE TABLE leads (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                obj_name TEXT,
                address TEXT,
                object_type TEXT,
                object_area REAL,
                customer_id TEXT,
                our_company_id TEXT,
                responsible_user_id TEXT,
                advance_percent REAL DEFAULT 0.0,
                vat_rate REAL DEFAULT 20.0,
                status TEXT DEFAULT 'incoming',
                total_value REAL DEFAULT 0.0,
                deal_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES companies (id),
                FOREIGN KEY (our_company_id) REFERENCES companies (id),
                FOREIGN KEY (responsible_user_id) REFERENCES users (id),
                FOREIGN KEY (deal_id) REFERENCES deals (id)
            )
        """))
        await session.commit()
        print("Leads table created")


async def ensure_leads_columns(session):
    result = await session.execute(text("PRAGMA table_info(leads)"))
    columns = {row[1] for row in result.fetchall()}
    if "responsible_user_id" not in columns:
        print("Adding responsible_user_id to leads...")
        await session.execute(text("ALTER TABLE leads ADD COLUMN responsible_user_id TEXT"))
        await session.commit()
        print("responsible_user_id added")
    if "vat_rate" not in columns:
        print("Adding vat_rate to leads...")
        await session.execute(text("ALTER TABLE leads ADD COLUMN vat_rate REAL DEFAULT 20.0"))
        await session.commit()
        print("vat_rate added")


async def create_lead_products_table():
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='lead_products'
        """))
        table_exists = result.fetchone()
        if table_exists:
            print("Lead products table already exists")
            return
        print("Creating lead_products table...")
        await session.execute(text("""
            CREATE TABLE lead_products (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                custom_name TEXT,
                custom_price REAL,
                quantity REAL DEFAULT 1.0,
                unit TEXT,
                unit_price REAL NOT NULL,
                discount_percent REAL DEFAULT 0.0,
                discount_amount REAL DEFAULT 0.0,
                tax_rate REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'RUB',
                total_price REAL,
                discount_total REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                final_price REAL,
                notes TEXT,
                custom_properties JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """))
        await session.commit()
        print("Lead products table created")


async def main():
    await create_leads_table()
    await create_lead_products_table()


if __name__ == "__main__":
    asyncio.run(main())
