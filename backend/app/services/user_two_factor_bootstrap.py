"""
Bootstrap helpers for user two-factor columns.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


REQUIRED_COLUMNS = {
    "two_factor_enabled": "ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0",
    "two_factor_secret_enc": "ALTER TABLE users ADD COLUMN two_factor_secret_enc VARCHAR(1024)",
    "two_factor_backup_codes_hash": "ALTER TABLE users ADD COLUMN two_factor_backup_codes_hash TEXT",
    "two_factor_enabled_at": "ALTER TABLE users ADD COLUMN two_factor_enabled_at DATETIME",
}


def ensure_user_two_factor_schema() -> None:
    inspector = inspect(engine_sync)
    if not inspector.has_table("users"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("users")}
    except Exception:
        columns = set()

    missing = [(name, ddl) for name, ddl in REQUIRED_COLUMNS.items() if name not in columns]
    if not missing:
        return

    with engine_sync.begin() as connection:
        for _, ddl in missing:
            connection.execute(text(ddl))
