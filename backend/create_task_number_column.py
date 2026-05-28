#!/usr/bin/env python3
"""
Add `number` column to `tasks` and backfill with sequential integers
ordered by `created_at` ASC (oldest task → #1).

Idempotent — safe to re-run.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def column_exists(conn, table: str, column: str) -> bool:
    """Try SQLite PRAGMA, then Postgres information_schema. Never raises."""
    try:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        rows = res.fetchall()
        # PRAGMA on SQLite returns at least 1 row when the table exists.
        # If we got rows back, this is SQLite and we can trust the result.
        if rows:
            return any(row[1] == column for row in rows)
        # No rows => either non-SQLite dialect OR table missing.
        # Try the Postgres path next.
    except Exception:
        pass
    try:
        res = await conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ), {"t": table, "c": column})
        return res.first() is not None
    except Exception:
        return False


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        # Best-effort idempotent ALTER. Both SQLite and Postgres raise on
        # duplicate column — we swallow that one specific case.
        try:
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN number INTEGER"))
            print("Added tasks.number column.")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                print("tasks.number already exists — skipping ALTER.")
            else:
                raise

        # Backfill: assign sequential numbers to rows where number IS NULL,
        # ordered by created_at ASC (then by id for tie-break stability).
        existing_max_res = await conn.execute(text("SELECT COALESCE(MAX(number), 0) FROM tasks"))
        existing_max = int(existing_max_res.scalar() or 0)

        rows_res = await conn.execute(text(
            "SELECT id FROM tasks WHERE number IS NULL ORDER BY created_at ASC, id ASC"
        ))
        ids = [r[0] for r in rows_res.fetchall()]
        if not ids:
            print("No tasks need backfill.")
        else:
            n = existing_max
            for task_id in ids:
                n += 1
                await conn.execute(
                    text("UPDATE tasks SET number = :n WHERE id = :id"),
                    {"n": n, "id": task_id},
                )
            print(f"Backfilled {len(ids)} tasks with sequential numbers ({existing_max + 1}..{n}).")

        # Try to add the UNIQUE index. Best-effort — if it fails (e.g. older
        # SQLite without explicit index name), the column still works.
        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_tasks_number_unique ON tasks(number)"
            ))
            print("Ensured unique index on tasks.number.")
        except Exception as e:
            print(f"Could not create unique index (non-fatal): {e}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
