#!/usr/bin/env python3
"""
Create M2M tables for task assignees and watchers.
Also backfills `task_assignees` from the legacy single
`tasks.assigned_to_user_id` column so existing tasks keep working.

Idempotent — safe to re-run.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models import Task, TaskAssignee, TaskWatcher


async def main():
    from app.core.config import settings

    database_url = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            TaskAssignee.__table__,
            TaskWatcher.__table__,
        ])
    print("task_assignees / task_watchers tables ensured.")

    # Backfill: any task with a legacy `assigned_to_user_id` and no
    # corresponding `task_assignees` row → insert one.
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    inserted = 0
    async with Session() as db:
        # Existing pairs (task_id, user_id) to avoid duplicates.
        existing_rows = (await db.execute(select(TaskAssignee.task_id, TaskAssignee.user_id))).all()
        existing = {(str(t), str(u)) for t, u in existing_rows}

        tasks_rows = (await db.execute(
            select(Task.id, Task.assigned_to_user_id).where(Task.assigned_to_user_id.isnot(None))
        )).all()

        for task_id, user_id in tasks_rows:
            key = (str(task_id), str(user_id))
            if key in existing:
                continue
            db.add(TaskAssignee(task_id=str(task_id), user_id=str(user_id)))
            existing.add(key)
            inserted += 1
        if inserted:
            await db.commit()
    print(f"Backfilled {inserted} task_assignees rows from legacy assigned_to_user_id.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
