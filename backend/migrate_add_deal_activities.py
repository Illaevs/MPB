#!/usr/bin/env python3
"""
Создаёт таблицу `deal_activities` для timeline-виджета на странице проекта
(аналог `lead_activities` для лидов).

Idempotent: если таблица уже есть — ничего не делает.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "deal_activities"):
            actions.append("deal_activities already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE deal_activities (
                    id VARCHAR(36) PRIMARY KEY,
                    deal_id VARCHAR(36) NOT NULL,
                    activity_type VARCHAR(32) NOT NULL,
                    content TEXT,
                    payload JSON,
                    actor_user_id VARCHAR(36),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals(id),
                    FOREIGN KEY (actor_user_id) REFERENCES users(id)
                )
                """
            ))
            conn.execute(text(
                "CREATE INDEX ix_deal_activities_deal_id ON deal_activities(deal_id)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_deal_activities_type ON deal_activities(activity_type)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_deal_activities_created_at ON deal_activities(created_at)"
            ))
            actions.append("deal_activities created")
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
