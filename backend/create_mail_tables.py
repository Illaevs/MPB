#!/usr/bin/env python3
"""
Create tables for mail integration.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base
from app.models import Mailbox, MailMessage


async def create_tables():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            Mailbox.__table__,
            MailMessage.__table__,
        ])

    print("Mail tables created successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
