#!/usr/bin/env python3
"""
Migration script to add contract documents and stage closing flag.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_contract_documents():
    async with async_session() as session:
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS contract_documents (
                    id TEXT PRIMARY KEY,
                    contract_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    number_in_contract INTEGER NOT NULL,
                    status TEXT DEFAULT 'draft',
                    pdf_file_name TEXT,
                    pdf_yandex_path TEXT,
                    edit_file_name TEXT,
                    edit_yandex_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES contracts (id)
                )
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_contract_documents_contract
                ON contract_documents(contract_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_contract_documents_type
                ON contract_documents(doc_type)
            """))
            await session.commit()
            print("Contract documents migrated")
        except Exception as exc:
            await session.rollback()
            if "duplicate column name" in str(exc).lower():
                print("Stage is_closed column already exists")
                return
            print(f"Migration failed: {exc}")
            raise
    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE stages ADD COLUMN is_closed INTEGER DEFAULT 0
            """))
            await session.commit()
            print("Stage column migrated")
        except Exception as exc:
            await session.rollback()
            if "duplicate column name" in str(exc).lower():
                print("Stage is_closed column already exists")
                return
            print(f"Stage migration failed: {exc}")
            raise


async def main():
    await migrate_contract_documents()


if __name__ == "__main__":
    asyncio.run(main())
