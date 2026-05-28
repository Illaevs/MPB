#!/usr/bin/env python3
"""
Add extra fields to legal cases and events.
"""
import asyncio

from sqlalchemy import text

from app.database.session import engine


async def migrate():
    statements = [
        "ALTER TABLE legal_cases ADD COLUMN jurisdiction VARCHAR(255)",
        "ALTER TABLE legal_cases ADD COLUMN judge_assistant VARCHAR(255)",
        "ALTER TABLE legal_cases ADD COLUMN judge_assistant_phone VARCHAR(50)",
        "ALTER TABLE legal_case_events ADD COLUMN event_time TIME",
        "ALTER TABLE legal_case_events ADD COLUMN courtroom VARCHAR(50)",
    ]

    async with engine.begin() as conn:
        for statement in statements:
            try:
                await conn.execute(text(statement))
            except Exception:
                pass

    print("Legal case fields migration completed.")


if __name__ == "__main__":
    asyncio.run(migrate())
