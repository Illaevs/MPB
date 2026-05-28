#!/usr/bin/env python3
"""
Create tables for legal work module and add task work_category column.
"""
import asyncio

from sqlalchemy import text

from app.database.base import Base
from app.database.session import engine, async_session
from app.models.legal_case import LegalCase, LegalCaseEvent, LegalCaseEventFile, LegalCaseTask


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            LegalCase.__table__,
            LegalCaseEvent.__table__,
            LegalCaseEventFile.__table__,
            LegalCaseTask.__table__,
        ])

    async with async_session() as session:
        try:
            await session.execute(text("ALTER TABLE tasks ADD COLUMN work_category VARCHAR(255)"))
            await session.commit()
        except Exception:
            await session.rollback()

    print("Legal work tables migration completed.")


if __name__ == "__main__":
    asyncio.run(create_tables())
