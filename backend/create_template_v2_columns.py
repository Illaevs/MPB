#!/usr/bin/env python3
"""
Add template_v2 columns to `document_templates`:
- layout_html         TEXT NULL       — HTML markup with locked/placeholder/editable sections
- editable_regions    JSON/TEXT NULL  — config for editable regions (MVP: single "body")
- placeholder_fields  JSON/TEXT NULL  — schema for the right-side parameters form

Idempotent — safe to re-run.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


COLUMNS = [
    ("layout_html", "TEXT"),
    ("editable_regions_json", "TEXT"),
    ("placeholder_fields_json", "TEXT"),
]


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        for column, ddl_type in COLUMNS:
            try:
                await conn.execute(text(f"ALTER TABLE document_templates ADD COLUMN {column} {ddl_type}"))
                print(f"Added document_templates.{column}")
            except Exception as e:
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    print(f"document_templates.{column} already exists — skipping.")
                else:
                    raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
