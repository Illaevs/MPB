#!/usr/bin/env python3
"""
Hotfix migration for production API 500 errors:
- /api/v1/accreditations/companies/{company_id}/documents
- /api/v1/legal-work/
- /api/v1/result-reviews

What it does (idempotent):
1) Ensures company_documents has storage_path and parent_id columns.
2) Ensures stage_results has storage_path column.
3) Backfills storage_path from yandex_path where possible.
4) Ensures legal_case_event_files table exists.
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
    if has_column(conn, table_name, column_name):
        return False
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_sql}"))
    return True


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        # 1) Ensure core accreditation tables exist.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_accreditations (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    direction_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_documents (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    doc_value TEXT,
                    file_name TEXT,
                    file_url TEXT,
                    storage_path TEXT,
                    parent_id TEXT,
                    status TEXT DEFAULT 'pending',
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (parent_id) REFERENCES company_documents (id)
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_company_documents_company_id ON company_documents(company_id)"
            )
        )

        # 2) Add missing columns to company_documents.
        if add_column_if_missing(conn, "company_documents", "storage_path", "TEXT"):
            actions.append("company_documents.storage_path added")
        if add_column_if_missing(conn, "company_documents", "parent_id", "TEXT"):
            actions.append("company_documents.parent_id added")

        # 3) stage_results: ensure storage_path exists (model expects it).
        if has_table(conn, "stage_results"):
            if add_column_if_missing(conn, "stage_results", "storage_path", "TEXT"):
                actions.append("stage_results.storage_path added")
        else:
            # Keep this minimal: if table is missing entirely, create shape required by router/model.
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS stage_results (
                        id TEXT PRIMARY KEY,
                        stage_id TEXT NOT NULL,
                        subcontractor_card_id TEXT NOT NULL,
                        deal_id TEXT,
                        product_name TEXT NOT NULL,
                        version_label TEXT NOT NULL,
                        version_number INTEGER,
                        comment TEXT,
                        reviewer_comment TEXT,
                        status TEXT DEFAULT 'review',
                        reviewer_id TEXT,
                        reviewed_at TIMESTAMP,
                        storage_path TEXT,
                        public_url TEXT,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                )
            )
            actions.append("stage_results table created")

        # 4) Backfill storage_path from yandex_path where this legacy column exists.
        if has_column(conn, "company_documents", "yandex_path") and has_column(
            conn, "company_documents", "storage_path"
        ):
            conn.execute(
                text(
                    """
                    UPDATE company_documents
                    SET storage_path = yandex_path
                    WHERE (storage_path IS NULL OR storage_path = '')
                      AND yandex_path IS NOT NULL
                      AND yandex_path <> ''
                    """
                )
            )
            actions.append("company_documents.storage_path backfilled from yandex_path")

        if has_column(conn, "stage_results", "yandex_path") and has_column(
            conn, "stage_results", "storage_path"
        ):
            conn.execute(
                text(
                    """
                    UPDATE stage_results
                    SET storage_path = yandex_path
                    WHERE (storage_path IS NULL OR storage_path = '')
                      AND yandex_path IS NOT NULL
                      AND yandex_path <> ''
                    """
                )
            )
            actions.append("stage_results.storage_path backfilled from yandex_path")

        # 5) legal_work files table required by /api/v1/legal-work list endpoint.
        # If legal_case_events exists, create with FK; otherwise create without FK to avoid hard fail.
        if has_table(conn, "legal_case_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS legal_case_event_files (
                        id TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        storage_path TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (event_id) REFERENCES legal_case_events (id) ON DELETE CASCADE
                    )
                    """
                )
            )
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS legal_case_event_files (
                        id TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        storage_path TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            actions.append("legal_case_events table missing: legal_case_event_files created without FK")

        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_legal_case_event_files_event_id ON legal_case_event_files(event_id)"
            )
        )

        # 6) Legal work core tables/columns used by router response.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS legal_cases (
                    id TEXT PRIMARY KEY,
                    case_number TEXT,
                    judge TEXT,
                    jurisdiction TEXT,
                    judge_assistant TEXT,
                    judge_assistant_phone TEXT,
                    plaintiff_id TEXT,
                    defendant_id TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS legal_case_events (
                    id TEXT PRIMARY KEY,
                    legal_case_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TIME,
                    courtroom TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS legal_case_tasks (
                    id TEXT PRIMARY KEY,
                    legal_case_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_legal_case_events_case_id ON legal_case_events(legal_case_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_legal_case_tasks_case_id ON legal_case_tasks(legal_case_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_legal_case_tasks_task_id ON legal_case_tasks(task_id)"
            )
        )

        if add_column_if_missing(conn, "legal_cases", "jurisdiction", "TEXT"):
            actions.append("legal_cases.jurisdiction added")
        if add_column_if_missing(conn, "legal_cases", "judge_assistant", "TEXT"):
            actions.append("legal_cases.judge_assistant added")
        if add_column_if_missing(conn, "legal_cases", "judge_assistant_phone", "TEXT"):
            actions.append("legal_cases.judge_assistant_phone added")
        if add_column_if_missing(conn, "legal_case_events", "event_time", "TIME"):
            actions.append("legal_case_events.event_time added")
        if add_column_if_missing(conn, "legal_case_events", "courtroom", "TEXT"):
            actions.append("legal_case_events.courtroom added")

    print("Hotfix migration completed.")
    if actions:
        print("Actions:")
        for item in actions:
            print(f"- {item}")
    else:
        print("No schema changes were required.")


if __name__ == "__main__":
    migrate()
