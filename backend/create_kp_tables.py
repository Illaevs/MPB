"""
Creates tables for commercial proposals (КП).
Supports both PostgreSQL and SQLite.
"""

import asyncio

from sqlalchemy import text

from app.database.session import engine


DDLS = [
    """
    CREATE TABLE IF NOT EXISTS kp_templates (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        docx_url TEXT NOT NULL,
        pdf_url TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kp_template_bindings (
        id VARCHAR(36) PRIMARY KEY,
        template_id VARCHAR(36) REFERENCES kp_templates(id) ON DELETE CASCADE,
        our_company_id VARCHAR(36) REFERENCES companies(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kp_documents (
        id VARCHAR(36) PRIMARY KEY,
        lead_id VARCHAR(36) REFERENCES leads(id) ON DELETE CASCADE,
        number_seq INTEGER NOT NULL,
        number_display VARCHAR(50) NOT NULL,
        status VARCHAR(50) DEFAULT 'draft',
        current_version INTEGER DEFAULT 1,
        our_company_id VARCHAR(36) REFERENCES companies(id),
        template_id VARCHAR(36) REFERENCES kp_templates(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kp_versions (
        id VARCHAR(36) PRIMARY KEY,
        kp_id VARCHAR(36) REFERENCES kp_documents(id) ON DELETE CASCADE,
        version INTEGER NOT NULL,
        docx_url TEXT,
        pdf_url TEXT,
        total_amount DOUBLE PRECISION DEFAULT 0,
        vat_amount DOUBLE PRECISION DEFAULT 0,
        total_text TEXT,
        vat_text TEXT,
        template_id VARCHAR(36) REFERENCES kp_templates(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


async def main():
    async with engine.begin() as conn:
        for ddl in DDLS:
            await conn.execute(text(ddl))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
