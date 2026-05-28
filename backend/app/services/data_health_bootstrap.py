from app.database.base import Base
from app.database.session import engine
from app.models.data_health_issue import DataHealthIssue
from sqlalchemy import inspect


REQUIRED_COLUMNS = {
    "ignored_reason": "ALTER TABLE data_health_issues ADD COLUMN ignored_reason TEXT",
    "ignored_until": "ALTER TABLE data_health_issues ADD COLUMN ignored_until DATETIME",
    "ignored_by_user_id": "ALTER TABLE data_health_issues ADD COLUMN ignored_by_user_id VARCHAR(36)",
    "ignored_at": "ALTER TABLE data_health_issues ADD COLUMN ignored_at DATETIME",
}


async def ensure_data_health_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[DataHealthIssue.__table__])
        existing_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("data_health_issues")}
        )
        for column_name, ddl in REQUIRED_COLUMNS.items():
            if column_name not in existing_columns:
                await conn.exec_driver_sql(ddl)
