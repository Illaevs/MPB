#!/usr/bin/env python3
"""
Create tables for consolidated document registry.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base
from app.models.document_registry import (
    Document,
    DocumentRelation,
    DocumentPackage,
    DocumentPackageItem,
    DocumentDispatch,
    DocumentDispatchChannel,
)


async def create_tables():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            Document.__table__,
            DocumentRelation.__table__,
            DocumentPackage.__table__,
            DocumentPackageItem.__table__,
            DocumentDispatch.__table__,
            DocumentDispatchChannel.__table__,
        ])

    print("Document registry tables created successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
