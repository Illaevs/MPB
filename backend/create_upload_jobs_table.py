#!/usr/bin/env python3
"""
Create upload_jobs table.
"""
import asyncio

from app.database.base import Base
from app.database.session import engine
from app.models.upload_job import UploadJob


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[UploadJob.__table__])

    print("Upload jobs table migration completed.")


if __name__ == "__main__":
    asyncio.run(create_tables())
