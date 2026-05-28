#!/usr/bin/env python3
"""
Migration script to create tasks table
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session

async def create_tasks_table():
    """Create tasks table"""
    async with async_session() as session:
        try:
            # Check if tasks table already exists
            result = await session.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'
            """))
            table_exists = result.fetchone()

            if table_exists:
                print("Tasks table already exists, dropping and recreating...")
                await session.execute(text("DROP TABLE tasks"))

            print("Creating tasks table...")

            # Create tasks table
            await session.execute(text("""
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    deal_id TEXT NOT NULL,
                    stage_id TEXT,
                    status TEXT DEFAULT 'new',
                    priority TEXT DEFAULT 'normal',
                    assigned_to_id TEXT,
                    created_by_id TEXT,
                    start_date DATE,
                    due_date DATE,
                    completed_at TIMESTAMP,
                    estimated_hours REAL DEFAULT 0.0,
                    actual_hours REAL DEFAULT 0.0,
                    tags TEXT,  -- JSON array
                    attachments TEXT,  -- JSON array
                    notify_assigned INTEGER DEFAULT 1,
                    notify_overdue INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals (id),
                    FOREIGN KEY (stage_id) REFERENCES stages (id),
                    FOREIGN KEY (assigned_to_id) REFERENCES companies (id),
                    FOREIGN KEY (created_by_id) REFERENCES companies (id)
                )
            """))

            await session.commit()
            print("Tasks table created successfully!")

        except Exception as e:
            print(f"Tasks table creation failed: {e}")
            await session.rollback()
            raise

async def main():
    print("Starting tasks table creation...")
    await create_tasks_table()
    print("Tasks table creation completed!")

if __name__ == "__main__":
    asyncio.run(main())
