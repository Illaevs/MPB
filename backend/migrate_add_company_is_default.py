#!/usr/bin/env python3
"""
Adds companies.is_default column for "our default company" selection.

When CRM has exactly one internal company, it must be the system-wide
fallback for our_company_id in leads/deals/projects/kp/documents.
The flag is the source of truth: GUI/helpers never guess by created_at.

Behavior on first run:
  - Adds the column with default 0 (false) if missing.
  - If there is exactly ONE company of type='internal', auto-promotes it
    to is_default=1 so the system doesn't sit in a half-broken state.
  - If there are zero or many, leaves the flag alone — admin chooses
    via UI (POST /api/v1/companies/{id}/set-default).

Idempotent: safe to run multiple times.
"""

from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def has_column(conn, table_name: str, column_name: str) -> bool:
    if not has_table(conn, table_name):
        return False
    columns = inspect(conn).get_columns(table_name)
    return any(col.get("name") == column_name for col in columns)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if not has_table(conn, "companies"):
            actions.append("companies table missing — skipping")
        elif not has_column(conn, "companies", "is_default"):
            # SQLite needs a literal default; Boolean is stored as INTEGER 0/1
            conn.execute(text(
                "ALTER TABLE companies ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0"
            ))
            actions.append("companies.is_default added")
        else:
            actions.append("companies.is_default already exists")

        # Auto-promote when exactly one internal company exists and no
        # default is set yet. This keeps single-company installs zero-touch.
        if has_table(conn, "companies") and has_column(conn, "companies", "is_default"):
            existing_default = conn.execute(text(
                "SELECT COUNT(*) FROM companies WHERE is_default = 1"
            )).scalar() or 0
            if existing_default == 0:
                internals = conn.execute(text(
                    "SELECT id FROM companies WHERE type = 'internal'"
                )).fetchall()
                if len(internals) == 1:
                    target_id = internals[0][0]
                    conn.execute(
                        text("UPDATE companies SET is_default = 1 WHERE id = :id"),
                        {"id": target_id},
                    )
                    actions.append(f"auto-promoted single internal company {target_id} to default")
                elif len(internals) == 0:
                    actions.append("no internal companies — pick one later via UI")
                else:
                    actions.append(
                        f"{len(internals)} internal companies — no default set, "
                        "choose one via POST /api/v1/companies/{id}/set-default"
                    )
            else:
                actions.append(f"{existing_default} default(s) already set — left as is")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
