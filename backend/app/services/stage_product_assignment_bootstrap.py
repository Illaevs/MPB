"""
Bootstrap helpers for stage_product_assignments schema.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


REQUIRED_COLUMNS = {
    "start_date": 'ALTER TABLE "stage_product_assignments" ADD COLUMN "start_date" DATE',
    "contract_due_date": 'ALTER TABLE "stage_product_assignments" ADD COLUMN "contract_due_date" DATE',
}


def ensure_stage_product_assignment_schema() -> None:
    inspector = inspect(engine_sync)
    if not inspector.has_table("stage_product_assignments"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("stage_product_assignments")}
    except Exception:
        columns = set()

    missing = [(name, ddl) for name, ddl in REQUIRED_COLUMNS.items() if name not in columns]

    with engine_sync.begin() as connection:
        for _, ddl in missing:
            connection.execute(text(ddl))
        connection.execute(
            text(
                """
                UPDATE stage_product_assignments
                SET start_date = (
                    SELECT s.date_start
                    FROM stages s
                    WHERE CAST(s.id AS TEXT) = CAST(stage_product_assignments.stage_id AS TEXT)
                       OR REPLACE(CAST(s.id AS TEXT), '-', '') = CAST(stage_product_assignments.stage_id AS TEXT)
                       OR CAST(s.id AS TEXT) = REPLACE(CAST(stage_product_assignments.stage_id AS TEXT), '-', '')
                    LIMIT 1
                )
                WHERE start_date IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE stage_product_assignments
                SET contract_due_date = due_date
                WHERE contract_due_date IS NULL AND due_date IS NOT NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE stage_product_assignments
                SET start_date = due_date
                WHERE start_date IS NULL AND due_date IS NOT NULL
                """
            )
        )
