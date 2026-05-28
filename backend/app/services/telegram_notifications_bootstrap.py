"""
Bootstrap helpers for Telegram notification schema.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.session import engine_sync
from app.models.notification_delivery import NotificationDelivery
from app.models.telegram_connection import TelegramConnection


RULES_REQUIRED_COLUMNS = {
    "deliver_telegram": "ALTER TABLE notification_rules ADD COLUMN deliver_telegram BOOLEAN DEFAULT 0",
}

PREFERENCES_REQUIRED_COLUMNS = {
    "deliver_telegram": "ALTER TABLE notification_preferences ADD COLUMN deliver_telegram BOOLEAN DEFAULT 0",
}

DEFAULT_TELEGRAM_TRIGGERS = (
    "task.assign",
    "task.overdue",
    "document.overdue",
)


def _ensure_table(table_name: str) -> None:
    table = Base.metadata.tables.get(table_name)
    if table is not None:
        table.create(bind=engine_sync, checkfirst=True)


def _ensure_columns(table_name: str, required_columns: dict[str, str]) -> tuple[bool, set[str]]:
    inspector = inspect(engine_sync)
    if not inspector.has_table(table_name):
        return False, set()

    try:
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    except Exception:
        existing_columns = set()

    missing = [(name, ddl) for name, ddl in required_columns.items() if name not in existing_columns]
    if not missing:
        return False, existing_columns

    with engine_sync.begin() as connection:
        for _, ddl in missing:
            connection.execute(text(ddl))

    return True, existing_columns | {name for name, _ in missing}


def ensure_telegram_notifications_schema() -> None:
    _ensure_table(TelegramConnection.__tablename__)
    _ensure_table(NotificationDelivery.__tablename__)

    rules_column_added, _ = _ensure_columns("notification_rules", RULES_REQUIRED_COLUMNS)
    _ensure_columns("notification_preferences", PREFERENCES_REQUIRED_COLUMNS)

    if rules_column_added:
        trigger_params = {f"trigger_{index}": value for index, value in enumerate(DEFAULT_TELEGRAM_TRIGGERS)}
        trigger_placeholders = ", ".join(f":trigger_{index}" for index, _ in enumerate(DEFAULT_TELEGRAM_TRIGGERS))
        with engine_sync.begin() as connection:
            connection.execute(
                text(
                    f"""
                    UPDATE notification_rules
                    SET deliver_telegram = 1
                    WHERE trigger IN ({trigger_placeholders})
                    """
                ),
                trigger_params,
            )
