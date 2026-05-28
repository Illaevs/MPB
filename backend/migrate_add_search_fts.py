#!/usr/bin/env python3
"""
Step 0 поиска: создание FTS5-индекса для полнотекстового поиска по
сущностям CRM.

Что создаём:
  • `search_fts` — virtual table FTS5 с tokenizer'ом `unicode61`
    (нормализация регистра, удаление диакритики — кириллица обрабатывается
    корректно). Колонки: entity_type, entity_id, title (boost ×3 в BM25),
    content (основное тело).
  • `search_index_meta` — обычная таблица с content_hash и last_indexed_at
    для идемпотентности (повторная индексация без изменений = no-op).
    Композитный PK (entity_type, entity_id).

Архитектура индексации:
  • Indexer-service подписан на ВСЕ `*.after_create/update/delete` через
    `@on` декоратор Event Bus (= первый реальный consumer V2).
  • При событии: вычисляем content_hash, если совпадает с прошлым — skip,
    иначе upsert в search_fts + обновляем meta.
  • Удаление: DELETE FROM search_fts WHERE entity_type=? AND entity_id=?
    + DELETE FROM search_index_meta.

Idempotent: пропускает таблицы если уже созданы.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        # 1. FTS5 virtual table. На SQLite модуль fts5 включён по умолчанию
        # в стандартных сборках. Tokenizer `unicode61 remove_diacritics 2`:
        #   • остаточные диакритические знаки удаляются (важно для русского,
        #     где «ё»→«е» удобно для поиска);
        #   • case-insensitive по дефолту.
        if has_table(conn, "search_fts"):
            actions.append("search_fts already exists")
        else:
            conn.execute(text(
                """
                CREATE VIRTUAL TABLE search_fts USING fts5(
                    entity_type UNINDEXED,
                    entity_id UNINDEXED,
                    title,
                    content,
                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            ))
            actions.append("search_fts created (FTS5 virtual table)")

        # 2. Meta-таблица для идемпотентности и observability.
        if has_table(conn, "search_index_meta"):
            actions.append("search_index_meta already exists")
        else:
            conn.execute(text(
                """
                CREATE TABLE search_index_meta (
                    entity_type VARCHAR(64) NOT NULL,
                    entity_id VARCHAR(64) NOT NULL,
                    content_hash VARCHAR(64) NOT NULL,
                    last_indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (entity_type, entity_id)
                )
                """
            ))
            # Индекс по hash — отладочный (поиск дублей).
            conn.execute(text(
                "CREATE INDEX ix_search_index_meta_hash ON search_index_meta(content_hash)"
            ))
            # Индекс по last_indexed_at — для bootstrap-скрипта (incremental).
            conn.execute(text(
                "CREATE INDEX ix_search_index_meta_indexed_at ON search_index_meta(last_indexed_at)"
            ))
            actions.append("search_index_meta created")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
