#!/usr/bin/env python3
"""
Migration script to add object_type and object_area columns to deals table
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session

async def migrate_deals_table():
    """Add new columns to deals table"""
    async with async_session() as session:
        try:
            # Check if columns already exist
            result = await session.execute(text("""
                PRAGMA table_info(deals)
            """))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            # Add object_type column if it doesn't exist
            if 'object_type' not in column_names:
                print("Adding object_type column...")
                await session.execute(text("""
                    ALTER TABLE deals ADD COLUMN object_type VARCHAR(100)
                """))

            # Add object_area column if it doesn't exist
            if 'object_area' not in column_names:
                print("Adding object_area column...")
                await session.execute(text("""
                    ALTER TABLE deals ADD COLUMN object_area FLOAT
                """))

            # Add vat_rate column if it doesn't exist
            if 'vat_rate' not in column_names:
                print("Adding vat_rate column...")
                await session.execute(text("""
                    ALTER TABLE deals ADD COLUMN vat_rate FLOAT DEFAULT 20.0
                """))

            # Add vat_included column if it doesn't exist
            if 'vat_included' not in column_names:
                print("Adding vat_included column...")
                await session.execute(text("""
                    ALTER TABLE deals ADD COLUMN vat_included BOOLEAN DEFAULT 1
                """))

            await session.commit()
            print("Deals migration completed successfully!")

        except Exception as e:
            print(f"Deals migration failed: {e}")
            await session.rollback()
            raise

async def migrate_deal_products_table():
    """Add new columns to deal_products table"""
    async with async_session() as session:
        try:
            # Check if columns already exist
            result = await session.execute(text("""
                PRAGMA table_info(deal_products)
            """))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            # Add custom_name column if it doesn't exist
            if 'custom_name' not in column_names:
                print("Adding custom_name column...")
                await session.execute(text("""
                    ALTER TABLE deal_products ADD COLUMN custom_name VARCHAR(255)
                """))

            # Add custom_price column if it doesn't exist
            if 'custom_price' not in column_names:
                print("Adding custom_price column...")
                await session.execute(text("""
                    ALTER TABLE deal_products ADD COLUMN custom_price FLOAT
                """))

            await session.commit()
            print("Deal products migration completed successfully!")

        except Exception as e:
            print(f"Deal products migration failed: {e}")
            await session.rollback()
            raise

async def main():
    print("Starting database migration...")
    await migrate_deals_table()
    await migrate_deal_products_table()
    print("All migrations completed!")

if __name__ == "__main__":
    asyncio.run(main())
