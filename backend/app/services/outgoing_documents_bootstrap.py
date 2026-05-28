"""
Bootstrap helpers for extended outgoing registry fields.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


REQUIRED_COLUMNS = {
    "document_kind": 'ALTER TABLE "outgoing_documents" ADD COLUMN "document_kind" VARCHAR(32) DEFAULT \'letter\' NOT NULL',
    "contract_id": 'ALTER TABLE "outgoing_documents" ADD COLUMN "contract_id" VARCHAR(36)',
    "bank_account_index": 'ALTER TABLE "outgoing_documents" ADD COLUMN "bank_account_index" INTEGER',
    "bank_account_snapshot": 'ALTER TABLE "outgoing_documents" ADD COLUMN "bank_account_snapshot" TEXT',
    "linked_stage_ids": 'ALTER TABLE "outgoing_documents" ADD COLUMN "linked_stage_ids" TEXT',
    "linked_payment_items": 'ALTER TABLE "outgoing_documents" ADD COLUMN "linked_payment_items" TEXT',
    "act_contract_document_id": 'ALTER TABLE "outgoing_documents" ADD COLUMN "act_contract_document_id" VARCHAR(36)',
    "recipient_genitive_name": 'ALTER TABLE "outgoing_documents" ADD COLUMN "recipient_genitive_name" VARCHAR(255)',
    "editor_mode": 'ALTER TABLE "outgoing_documents" ADD COLUMN "editor_mode" VARCHAR(32) DEFAULT \'classic\'',
    "editor_schema_version": 'ALTER TABLE "outgoing_documents" ADD COLUMN "editor_schema_version" INTEGER DEFAULT 1',
    "editor_draft_json": 'ALTER TABLE "outgoing_documents" ADD COLUMN "editor_draft_json" TEXT',
    "editor_validation_json": 'ALTER TABLE "outgoing_documents" ADD COLUMN "editor_validation_json" TEXT',
    "editor_render_context_json": 'ALTER TABLE "outgoing_documents" ADD COLUMN "editor_render_context_json" TEXT',
}


def ensure_outgoing_documents_schema() -> None:
    inspector = inspect(engine_sync)
    if not inspector.has_table("outgoing_documents"):
        return

    try:
        columns = {column["name"] for column in inspector.get_columns("outgoing_documents")}
    except Exception:
        columns = set()

    with engine_sync.begin() as connection:
        for column_name, ddl in REQUIRED_COLUMNS.items():
            if column_name not in columns:
                connection.execute(text(ddl))

        if "document_kind" not in columns:
            connection.execute(text("UPDATE outgoing_documents SET document_kind = 'letter' WHERE document_kind IS NULL"))
        if "editor_mode" not in columns:
            connection.execute(text("UPDATE outgoing_documents SET editor_mode = 'classic' WHERE editor_mode IS NULL"))
        if "editor_schema_version" not in columns:
            connection.execute(text("UPDATE outgoing_documents SET editor_schema_version = 1 WHERE editor_schema_version IS NULL"))
