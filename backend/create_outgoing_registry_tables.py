#!/usr/bin/env python3
"""
Migration script to create outgoing registry tables.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def _table_exists(session, table_name: str) -> bool:
    result = await session.execute(text("""
        SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


async def migrate_outgoing_registry():
    async with async_session() as session:
        try:
            if not await _table_exists(session, "outgoing_number_sequences"):
                await session.execute(text("""
                    CREATE TABLE outgoing_number_sequences (
                        our_company_key TEXT PRIMARY KEY,
                        next_seq INTEGER NOT NULL DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """))
                print("Created outgoing_number_sequences table")

            if not await _table_exists(session, "outgoing_documents"):
                await session.execute(text("""
                    CREATE TABLE outgoing_documents (
                        id TEXT PRIMARY KEY,
                        outgoing_number_seq INTEGER NOT NULL,
                        outgoing_number TEXT NOT NULL,
                        recipient_company_id TEXT NOT NULL,
                        deal_id TEXT,
                        letter_date DATE NOT NULL,
                        subject TEXT NOT NULL,
                        body TEXT,
                        attachments_list TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (recipient_company_id) REFERENCES companies (id),
                        FOREIGN KEY (deal_id) REFERENCES deals (id)
                    )
                """))
                print("Created outgoing_documents table")

            if not await _table_exists(session, "outgoing_document_versions"):
                await session.execute(text("""
                    CREATE TABLE outgoing_document_versions (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        version_number INTEGER NOT NULL,
                        status TEXT DEFAULT 'draft',
                        created_by TEXT,
                        comment TEXT,
                        pdf_path TEXT,
                        pdf_public_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES outgoing_documents (id)
                    )
                """))
                print("Created outgoing_document_versions table")

            if not await _table_exists(session, "outgoing_document_files"):
                await session.execute(text("""
                    CREATE TABLE outgoing_document_files (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        version_id TEXT,
                        file_type TEXT DEFAULT 'attachment',
                        file_path TEXT,
                        file_name TEXT,
                        public_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES outgoing_documents (id),
                        FOREIGN KEY (version_id) REFERENCES outgoing_document_versions (id)
                    )
                """))
                print("Created outgoing_document_files table")

            await session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_outgoing_documents_number
                ON outgoing_documents(outgoing_number)
            """))
            await session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_outgoing_documents_seq
                ON outgoing_documents(outgoing_number_seq)
            """))
            print("Ensured unique indexes for outgoing documents")

            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_outgoing_registry()


if __name__ == "__main__":
    asyncio.run(main())
