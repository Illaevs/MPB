"""
Bootstrap helpers for contract document amount and invoice-product links.
"""
from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.session import engine_sync
from app.models.contract_document_product_link import ContractDocumentProductLink


REQUIRED_COLUMNS = {
    "amount": 'ALTER TABLE "contract_documents" ADD COLUMN "amount" FLOAT',
}


def ensure_contract_documents_schema() -> None:
    inspector = inspect(engine_sync)
    if not inspector.has_table("contract_documents"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("contract_documents")}
    except Exception:
        columns = set()

    with engine_sync.begin() as connection:
        for column_name, ddl in REQUIRED_COLUMNS.items():
            if column_name not in columns:
                connection.execute(text(ddl))

    Base.metadata.create_all(engine_sync, tables=[ContractDocumentProductLink.__table__])
