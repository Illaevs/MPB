#!/usr/bin/env python3
"""
Creates the `task_reads` table for per-user "last read" markers on task
chat threads. Used to compute unread message counts in the task list /
kanban indicators.

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "task_reads"):
            actions.append("task_reads already exists")
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE task_reads (
                        user_id VARCHAR(36) NOT NULL,
                        task_id VARCHAR(36) NOT NULL,
                        last_read_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        PRIMARY KEY (user_id, task_id),
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (task_id) REFERENCES tasks(id)
                    )
                    """
                )
            )
            actions.append("task_reads created")
        # Index supporting the unread-counts query (filter by user + join
        # to task_messages on task_id).
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_task_reads_user_id ON task_reads(user_id)"
                )
            )
            actions.append("ix_task_reads_user_id ensured")
        except Exception as exc:  # pragma: no cover - non-SQLite engines
            actions.append(f"ix_task_reads_user_id skip: {exc}")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
