#!/usr/bin/env python3
"""
Add KPP field to companies.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import inspect, text

from app.database.session import async_session, engine


async def migrate_company_kpp():
    async with engine.begin() as conn:
        def has_kpp(sync_conn):
            inspector = inspect(sync_conn)
            return "kpp" in {column["name"] for column in inspector.get_columns("companies")}

        exists = await conn.run_sync(has_kpp)
        if not exists:
            await conn.execute(text("ALTER TABLE companies ADD COLUMN kpp VARCHAR(20)"))


async def main():
    await migrate_company_kpp()
    async with async_session() as session:
        await session.commit()
    print("Company KPP migrated")


if __name__ == "__main__":
    asyncio.run(main())
