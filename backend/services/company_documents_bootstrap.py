"""
Bootstrap helpers for company_documents schema.
"""
from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.session import engine_sync
from app.models.company_document import CompanyDocument


REQUIRED_COLUMNS = {
    "our_company_id": 'ALTER TABLE "company_documents" ADD COLUMN "our_company_id" VARCHAR(36)',
    "file_size": 'ALTER TABLE "company_documents" ADD COLUMN "file_size" INTEGER',
    "content_type": 'ALTER TABLE "company_documents" ADD COLUMN "content_type" VARCHAR(255)',
}


def ensure_company_documents_schema() -> None:
    Base.metadata.create_all(engine_sync, tables=[CompanyDocument.__table__])
    inspector = inspect(engine_sync)
    if not inspector.has_table("company_documents"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("company_documents")}
    except Exception:
        columns = set()

    with engine_sync.begin() as connection:
        for column_name, ddl in REQUIRED_COLUMNS.items():
            if column_name not in columns:
                connection.execute(text(ddl))
