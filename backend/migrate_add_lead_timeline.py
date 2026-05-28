#!/usr/bin/env python3
"""
Adds `lead_activities` table (timeline feed for leads, Bitrix-style)
and `tasks.lead_id` column for linking tasks directly to a lead.

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, name: str) -> bool:
    return inspect(conn).has_table(name)


def has_column(conn, table: str, column: str) -> bool:
    if not has_table(conn, table):
        return False
    cols = inspect(conn).get_columns(table)
    return any(c.get("name") == column for c in cols)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        dialect = conn.dialect.name

        # 1. lead_activities table
        if not has_table(conn, "lead_activities"):
            if dialect == "postgresql":
                conn.execute(text("""
                    CREATE TABLE lead_activities (
                        id VARCHAR(36) PRIMARY KEY,
                        lead_id VARCHAR(36) NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                        activity_type VARCHAR(32) NOT NULL,
                        content TEXT,
                        payload JSONB DEFAULT '{}'::jsonb,
                        actor_user_id VARCHAR(36),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """))
                conn.execute(text("CREATE INDEX ix_lead_activities_lead_id ON lead_activities(lead_id)"))
                conn.execute(text("CREATE INDEX ix_lead_activities_activity_type ON lead_activities(activity_type)"))
                conn.execute(text("CREATE INDEX ix_lead_activities_created_at ON lead_activities(created_at DESC)"))
            else:
                conn.execute(text("""
                    CREATE TABLE lead_activities (
                        id VARCHAR(36) PRIMARY KEY,
                        lead_id VARCHAR(36) NOT NULL,
                        activity_type VARCHAR(32) NOT NULL,
                        content TEXT,
                        payload JSON,
                        actor_user_id VARCHAR(36),
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (lead_id) REFERENCES leads(id)
                    )
                """))
                conn.execute(text("CREATE INDEX ix_lead_activities_lead_id ON lead_activities(lead_id)"))
                conn.execute(text("CREATE INDEX ix_lead_activities_activity_type ON lead_activities(activity_type)"))
                conn.execute(text("CREATE INDEX ix_lead_activities_created_at ON lead_activities(created_at)"))
            actions.append("lead_activities table created")
        else:
            actions.append("lead_activities already exists")

        # 2. tasks.lead_id
        if has_table(conn, "tasks") and not has_column(conn, "tasks", "lead_id"):
            conn.execute(text("ALTER TABLE tasks ADD COLUMN lead_id VARCHAR(36)"))
            try:
                conn.execute(text("CREATE INDEX ix_tasks_lead_id ON tasks(lead_id)"))
            except Exception:
                pass
            actions.append("tasks.lead_id added")
        else:
            actions.append("tasks.lead_id already exists or table missing")

    print("\n".join(actions))


if __name__ == "__main__":
    migrate()
