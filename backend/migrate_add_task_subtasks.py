#!/usr/bin/env python3
"""
Creates the `task_subtasks` table — чек-лист / подзадачи внутри задачи.

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "task_subtasks"):
            actions.append("task_subtasks already exists")
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE task_subtasks (
                        id VARCHAR(36) PRIMARY KEY,
                        task_id VARCHAR(36) NOT NULL,
                        title TEXT NOT NULL,
                        is_done BOOLEAN NOT NULL DEFAULT 0,
                        assigned_to_user_id VARCHAR(36),
                        due_date DATE,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        created_by_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME,
                        done_at DATETIME,
                        FOREIGN KEY (task_id) REFERENCES tasks(id),
                        FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
                        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
                    )
                    """
                )
            )
            actions.append("task_subtasks created")
        # Индекс на task_id — все CRUD-эндпоинты сначала фильтруют по
        # этой колонке (loadByTask, reorder, count). Без него каждая
        # выборка делает full scan.
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_task_subtasks_task_id ON task_subtasks(task_id)"
                )
            )
            actions.append("ix_task_subtasks_task_id ensured")
        except Exception as exc:  # pragma: no cover
            actions.append(f"ix_task_subtasks_task_id skip: {exc}")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
