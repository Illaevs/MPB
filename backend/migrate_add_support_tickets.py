#!/usr/bin/env python3
"""
Creates support_tickets / support_messages tables for the
«Тех. поддержка» ticket system.

Idempotent: create(checkfirst=True) skips existing tables.
"""

from app.core.config import settings  # noqa: F401  (env-aware: AUTO_MIGRATE
# discovery picks this up; engine_sync targets settings.SQLALCHEMY_DATABASE_URI)
from app.database.session import engine_sync
from app.models.support_ticket import SupportTicket, SupportMessage

_ = settings.SQLALCHEMY_DATABASE_URI


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        for model in (SupportTicket, SupportMessage):
            table = model.__table__
            existed = engine_sync.dialect.has_table(conn, table.name)
            table.create(bind=conn, checkfirst=True)
            actions.append(
                f"{table.name} {'already exists' if existed else 'created'}"
            )
    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
