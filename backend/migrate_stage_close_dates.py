#!/usr/bin/env python3
"""
Add close_date to stage tables and backfill existing closed stages.

Idempotent migration:
1. Adds `close_date` to `stages` if missing.
2. Adds `close_date` to `subcontractor_stages` if missing.
3. Backfills `close_date = date_end` for already closed/completed stages.
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


def add_column_if_missing(conn, table_name: str, column_name: str, column_type_sql: str) -> bool:
    if not has_table(conn, table_name) or has_column(conn, table_name, column_name):
        return False
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_sql}"))
    return True


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if add_column_if_missing(conn, "stages", "close_date", "DATE"):
            actions.append("stages.close_date added")

        if add_column_if_missing(conn, "subcontractor_stages", "close_date", "DATE"):
            actions.append("subcontractor_stages.close_date added")

        if has_table(conn, "stages") and has_column(conn, "stages", "close_date"):
            conn.execute(
                text(
                    """
                    UPDATE stages
                    SET close_date = date_end
                    WHERE close_date IS NULL
                      AND date_end IS NOT NULL
                      AND status = 'completed'
                    """
                )
            )
            actions.append("stages.close_date backfilled from completed status")

            if has_column(conn, "stages", "is_closed"):
                conn.execute(
                    text(
                        """
                        UPDATE stages
                        SET close_date = date_end
                        WHERE close_date IS NULL
                          AND date_end IS NOT NULL
                          AND is_closed = :true_value
                        """
                    ),
                    {"true_value": True},
                )
                actions.append("stages.close_date backfilled from is_closed")

        if has_table(conn, "subcontractor_stages") and has_column(conn, "subcontractor_stages", "close_date"):
            conn.execute(
                text(
                    """
                    UPDATE subcontractor_stages
                    SET close_date = date_end
                    WHERE close_date IS NULL
                      AND date_end IS NOT NULL
                      AND status = 'completed'
                    """
                )
            )
            actions.append("subcontractor_stages.close_date backfilled from completed status")

    if actions:
        print("Stage close date migration complete:")
        for action in actions:
            print(f"- {action}")
    else:
        print("Stage close date migration already applied.")


if __name__ == "__main__":
    migrate()
