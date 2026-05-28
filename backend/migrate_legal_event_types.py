#!/usr/bin/env python3
"""
Migration script to update legal work event type names.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


OLD_TYPE = "\u0420\u0435\u0448\u0435\u043d\u0438\u0435"
NEW_TYPE = "\u0420\u0435\u0437\u043e\u043b\u044e\u0442\u0438\u0432\u043d\u0430\u044f \u0447\u0430\u0441\u0442\u044c \u0440\u0435\u0448\u0435\u043d\u0438\u044f"


async def migrate_event_types():
    async with async_session() as session:
        try:
            result = await session.execute(
                text(
                    """
                    UPDATE legal_case_events
                    SET event_type = :new_type
                    WHERE event_type = :old_type
                    """
                ),
                {"new_type": NEW_TYPE, "old_type": OLD_TYPE},
            )
            await session.commit()
            print(f"Updated {result.rowcount} event(s)")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise


async def main():
    await migrate_event_types()


if __name__ == "__main__":
    asyncio.run(main())
