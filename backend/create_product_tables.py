#!/usr/bin/env python3
"""
Script to create product catalog tables in the database
"""
import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.deal_product import DealProduct

async def create_tables():
    """Create the product catalog tables"""
    # Get database URL from config
    from app.core.config import settings

    # Create async engine
    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    # Create tables
    async with engine.begin() as conn:
        # Create tables for product catalog
        await conn.run_sync(Base.metadata.create_all, tables=[
            ProductCategory.__table__,
            Product.__table__,
            DealProduct.__table__
        ])

    print("Product catalog tables created successfully!")

    # Close the engine
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
