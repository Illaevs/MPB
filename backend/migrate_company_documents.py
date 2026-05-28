#!/usr/bin/env python3
"""
Migration script to update company_documents table for versions and Yandex paths.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_company_documents():
    async with async_session() as session:
        try:
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='company_documents'
            """))
            table_exists = result.fetchone()
            if not table_exists:
                await session.execute(text("""
                    CREATE TABLE company_documents (
                        id TEXT PRIMARY KEY,
                        company_id TEXT NOT NULL,
                        doc_type TEXT NOT NULL,
                        doc_value TEXT,
                        file_name TEXT,
                        file_url TEXT,
                        yandex_path TEXT,
                        parent_id TEXT,
                        status TEXT DEFAULT 'pending',
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id),
                        FOREIGN KEY (parent_id) REFERENCES company_documents (id)
                    )
                """))
            else:
                columns_result = await session.execute(text("PRAGMA table_info(company_documents)"))
                columns = {row[1] for row in columns_result.fetchall()}
                if "yandex_path" not in columns:
                    await session.execute(text("ALTER TABLE company_documents ADD COLUMN yandex_path TEXT"))
                if "parent_id" not in columns:
                    await session.execute(text("ALTER TABLE company_documents ADD COLUMN parent_id TEXT"))

            await session.commit()
            print("Company documents migrated")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_company_documents()


if __name__ == "__main__":
    asyncio.run(main())
