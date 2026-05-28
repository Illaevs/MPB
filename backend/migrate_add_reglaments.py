#!/usr/bin/env python3
"""
Reglaments Phase 0: нормативная база (СНиП/ГОСТ/СП) для генпроектирования.

Создаём ИЗОЛИРОВАННЫЙ домен — отдельный от основного `search_fts` /
`search_embeddings`. Это намеренное архитектурное решение, чтобы:
  • не разбавлять основной поиск (deals/tasks/...) тысячами строк нормативки;
  • можно было фильтровать/ранжировать нормы по своим правилам
    (doc_type, status, discipline) — не мешая бизнес-сущностям;
  • удалить или переиндексировать всю нормативную базу одним SQL-ом
    без побочных эффектов на индекс CRM.

Таблицы:
  • `reglaments` — header (СП 63.13330.2018, СНиП II-3-79, ГОСТ 31937, ...).
  • `reglament_sections` — chunks: разделы документа (5.4.2, 7.1.1, ...)
    — каждая секция отдельная единица для FTS + embedding.
  • `reglament_fts` — FTS5 virtual table (BM25-поиск по секциям).
  • `reglament_embeddings` — BLOB-cosine (по аналогии с search_embeddings).
  • `reglament_index_meta` — content_hash идемпотентности.

Идемпотентно: пропускает таблицы если уже созданы.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        # 1. Header — собственно нормативный документ.
        if has_table(conn, "reglaments"):
            actions.append("reglaments already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE reglaments (
                    id VARCHAR(36) PRIMARY KEY,
                    doc_type VARCHAR(16) NOT NULL,
                    doc_number VARCHAR(64) NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    full_title TEXT,
                    status VARCHAR(32) NOT NULL DEFAULT 'actual',
                    effective_date DATE,
                    cancelled_date DATE,
                    replaced_by_id VARCHAR(36),
                    discipline_tags VARCHAR(256),
                    source_url VARCHAR(512),
                    page_count INTEGER,
                    section_count INTEGER DEFAULT 0,
                    full_text_size INTEGER DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (replaced_by_id) REFERENCES reglaments(id) ON DELETE SET NULL
                )
                """
            ))
            conn.execute(text("CREATE INDEX ix_reglaments_doc_type ON reglaments(doc_type)"))
            conn.execute(text("CREATE INDEX ix_reglaments_doc_number ON reglaments(doc_number)"))
            conn.execute(text("CREATE INDEX ix_reglaments_status ON reglaments(status)"))
            conn.execute(text(
                "CREATE UNIQUE INDEX ux_reglaments_type_number ON reglaments(doc_type, doc_number)"
            ))
            actions.append("reglaments created")

        # 2. Секции документа (chunks для индексации).
        if has_table(conn, "reglament_sections"):
            actions.append("reglament_sections already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE reglament_sections (
                    id VARCHAR(36) PRIMARY KEY,
                    reglament_id VARCHAR(36) NOT NULL,
                    section_number VARCHAR(32),
                    section_title VARCHAR(512),
                    content TEXT NOT NULL,
                    parent_section_id VARCHAR(36),
                    order_idx INTEGER NOT NULL DEFAULT 0,
                    char_count INTEGER DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reglament_id) REFERENCES reglaments(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_section_id) REFERENCES reglament_sections(id) ON DELETE CASCADE
                )
                """
            ))
            conn.execute(text(
                "CREATE INDEX ix_reglament_sections_reglament_id ON reglament_sections(reglament_id, order_idx)"
            ))
            actions.append("reglament_sections created")

        # 3. FTS5 — собственный индекс, ИЗОЛИРОВАН от search_fts.
        if has_table(conn, "reglament_fts"):
            actions.append("reglament_fts already exists")
        else:
            conn.execute(text(
                """
                CREATE VIRTUAL TABLE reglament_fts USING fts5(
                    section_id UNINDEXED,
                    reglament_id UNINDEXED,
                    doc_number UNINDEXED,
                    doc_type UNINDEXED,
                    section_number,
                    section_title,
                    content,
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            ))
            actions.append("reglament_fts created (FTS5)")

        # 4. Embeddings — BLOB-cosine для семантического матчинга по нормам.
        if has_table(conn, "reglament_embeddings"):
            actions.append("reglament_embeddings already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE reglament_embeddings (
                    section_id VARCHAR(36) PRIMARY KEY,
                    reglament_id VARCHAR(36) NOT NULL,
                    model_name VARCHAR(128) NOT NULL,
                    dim INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    content_hash VARCHAR(64) NOT NULL,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (section_id) REFERENCES reglament_sections(id) ON DELETE CASCADE
                )
                """
            ))
            conn.execute(text(
                "CREATE INDEX ix_reglament_embeddings_reglament_id ON reglament_embeddings(reglament_id)"
            ))
            conn.execute(text(
                "CREATE INDEX ix_reglament_embeddings_model ON reglament_embeddings(model_name, dim)"
            ))
            actions.append("reglament_embeddings created")

        # 5. Meta для идемпотентности.
        if has_table(conn, "reglament_index_meta"):
            actions.append("reglament_index_meta already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE reglament_index_meta (
                    section_id VARCHAR(36) PRIMARY KEY,
                    content_hash VARCHAR(64) NOT NULL,
                    last_indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))
            actions.append("reglament_index_meta created")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
