#!/usr/bin/env python3
"""
Migration script to update document registry tables.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_document_registry():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='documents'
            """))
            if not result.fetchone():
                await session.execute(text("""
                    CREATE TABLE documents (
                        id TEXT PRIMARY KEY,
                        doc_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        number TEXT,
                        document_date DATE,
                        status TEXT,
                        project_id TEXT,
                        counterparty_id TEXT,
                        our_company_id TEXT,
                        source_type TEXT,
                        source_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
            else:
                columns = await session.execute(text("PRAGMA table_info(documents)"))
                column_names = {row[1] for row in columns.fetchall()}
                if "our_company_id" not in column_names:
                    await session.execute(text("ALTER TABLE documents ADD COLUMN our_company_id TEXT"))

            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='document_packages'
            """))
            if not result.fetchone():
                await session.execute(text("""
                    CREATE TABLE document_packages (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        package_date DATE,
                        status TEXT,
                        project_id TEXT,
                        counterparty_id TEXT,
                        our_company_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            else:
                columns = await session.execute(text("PRAGMA table_info(document_packages)"))
                column_names = {row[1] for row in columns.fetchall()}
                if "our_company_id" not in column_names:
                    await session.execute(text("ALTER TABLE document_packages ADD COLUMN our_company_id TEXT"))

            await session.commit()
            print("Document registry migration completed")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_document_registry()


if __name__ == "__main__":
    asyncio.run(main())
