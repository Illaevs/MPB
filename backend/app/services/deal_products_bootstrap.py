"""
Bootstrap helpers for deal_products schema.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


REQUIRED_COLUMNS = {
    "tax_included": 'ALTER TABLE "deal_products" ADD COLUMN "tax_included" BOOLEAN DEFAULT FALSE',
}


def ensure_deal_products_schema() -> None:
    inspector = inspect(engine_sync)
    if not inspector.has_table("deal_products"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("deal_products")}
    except Exception:
        columns = set()

    with engine_sync.begin() as connection:
        for column_name, ddl in REQUIRED_COLUMNS.items():
            if column_name not in columns:
                connection.execute(text(ddl))
