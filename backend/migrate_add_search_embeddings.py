#!/usr/bin/env python3
"""
Step 1 поиска: создание вектора embedding'ов для семантического поиска.

Что создаём:
  • `search_embeddings` — обычная таблица с BLOB-колонкой `embedding`.
    Колонки: entity_type, entity_id, model_name, dim, embedding (BLOB),
    content_hash (для синхронизации с FTS), updated_at.
    PK: (entity_type, entity_id).
  • Опционально: vec0-virtual-table из sqlite-vec, если extension доступен
    (нужен в runtime для быстрого ANN-search). Если sqlite-vec не загружен —
    fallback на brute-force cosine через NumPy в Python.

Архитектура:
  • Embedding-worker (отдельный процесс) подписывается на event_outbox
    (тот же паттерн что webhook-worker). При появлении новой строки
    в outbox с типом `*.after_*` для индексируемой сущности — генерирует
    embedding через `sentence-transformers` и UPSERT'ит в search_embeddings.
  • Поиск (`hybrid` режим): первый этап — FTS5 BM25 (top-200), второй
    этап — cosine между embedding(query) и embeddings(candidates),
    объединение через RRF (Reciprocal Rank Fusion).

Идемпотентность: пропускает таблицу если уже создана.
"""
from sqlalchemy import inspect, text

from app.database.session import engine_sync


def has_table(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def migrate() -> None:
    actions = []
    with engine_sync.begin() as conn:
        if has_table(conn, "search_embeddings"):
            actions.append("search_embeddings already exists")
        else:
            # Обычная таблица — vec0-extension опционален и грузится в
            # runtime в embedding_worker'е. Если extension недоступен,
            # cosine считается brute-force через NumPy (медленнее, но
            # работает; до ~10k записей разница незаметна).
            conn.execute(text(
                """
                CREATE TABLE search_embeddings (
                    entity_type VARCHAR(64) NOT NULL,
                    entity_id VARCHAR(64) NOT NULL,
                    model_name VARCHAR(128) NOT NULL,
                    dim INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    content_hash VARCHAR(64) NOT NULL,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (entity_type, entity_id)
                )
                """
            ))
            # Индекс по model_name + dim — отладочный (миграция между
            # моделями: новые embeddings с другим dim лежат рядом).
            conn.execute(text(
                "CREATE INDEX ix_search_embeddings_model ON search_embeddings(model_name, dim)"
            ))
            # Индекс по entity_type — для bootstrap (батч по типам).
            conn.execute(text(
                "CREATE INDEX ix_search_embeddings_entity_type ON search_embeddings(entity_type)"
            ))
            actions.append("search_embeddings created (BLOB-based cosine)")

    print("\n".join(actions) or "no changes")


if __name__ == "__main__":
    migrate()
