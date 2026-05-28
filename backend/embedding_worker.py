"""
Step 1 поиска: embedding-worker (отдельный процесс).

Что делает:
  • Поллит `event_outbox` (тот же паттерн что `event_outbox_worker.py`).
  • Для строк типа `<entity>.after_create/update/...` где entity_type
    есть в `search_indexer.EXTRACTORS`:
       1) извлекает свежий title+content через те же экстракторы;
       2) lazy-load модели при первом задании;
       3) вычисляет embedding;
       4) UPSERT'ит в `search_embeddings` с content_hash из FTS-индекса
          (синхронизация: если hash совпал — skip, повторная работа не
          выполняется).
  • Memory isolation: запускается как ОТДЕЛЬНЫЙ процесс. Если worker
    падает (OOM при загрузке модели, segfault native) — FastAPI и
    основной outbox-worker продолжают работу.

Lazy model load:
  • Модель грузится при первом задании, удерживается в памяти.
  • Auto-unload через `EMBEDDING_IDLE_UNLOAD_SECS` (по умолчанию 900с =
    15 мин) если новых заданий не было.
  • Так в idle worker занимает ~100 МБ, в активном ~3 ГБ (bge-m3 FP16).

Запуск:
  python embedding_worker.py

ENV:
  EMBEDDING_MODEL              — id модели на HuggingFace (по умолчанию
                                 BAAI/bge-m3, fallback intfloat/multilingual-e5-base)
  EMBEDDING_POLL_INTERVAL_SECS — пауза между опросами outbox (default 2.0)
  EMBEDDING_IDLE_UNLOAD_SECS   — выгрузка модели после простоя (default 900)
  EMBEDDING_BATCH_SIZE         — сколько событий за один тик (default 32)
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import signal
import struct
import sys
import time
from typing import Any, List, Optional

# Логирование настраиваем рано, до тяжёлых импортов.
logging.basicConfig(
    level=os.environ.get("EMBEDDING_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("embedding_worker")

# SECRET_KEY должен быть установлен для запуска FastAPI-зависимых модулей.
os.environ.setdefault("SECRET_KEY", "x" * 64)

MODEL_ID = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
POLL_INTERVAL = float(os.environ.get("EMBEDDING_POLL_INTERVAL_SECS", "2.0"))
IDLE_UNLOAD = float(os.environ.get("EMBEDDING_IDLE_UNLOAD_SECS", "900"))
BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "32"))

_RUNNING = True


def _stop_signal(signum, frame):
    global _RUNNING
    logger.info("Received signal %s, stopping after current batch", signum)
    _RUNNING = False


signal.signal(signal.SIGINT, _stop_signal)
signal.signal(signal.SIGTERM, _stop_signal)


# ────────────────────────────────────────────────────────────────────
# Lazy model holder
# ────────────────────────────────────────────────────────────────────

class _ModelHolder:
    """Lazy-load модели + auto-unload при простое.

    Хранит SentenceTransformer-инстанс. .encode() возвращает np.ndarray.
    """

    def __init__(self, model_id: str, idle_unload_secs: float):
        self.model_id = model_id
        self.idle_unload_secs = idle_unload_secs
        self._model: Optional[Any] = None
        self._last_used_at: float = 0.0
        self._dim: Optional[int] = None
        self._load_lock = asyncio.Lock()

    async def get(self):
        async with self._load_lock:
            if self._model is None:
                logger.info("Loading embedding model: %s", self.model_id)
                started = time.monotonic()
                # Импорт лениво — torch грузится только когда реально нужно.
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_id, device="cpu")
                # Probe dim
                probe = self._model.encode(["probe"], normalize_embeddings=True)
                self._dim = int(probe.shape[-1])
                elapsed = time.monotonic() - started
                logger.info("Model loaded (dim=%d) in %.1fs", self._dim, elapsed)
        self._last_used_at = time.monotonic()
        return self._model

    @property
    def dim(self) -> Optional[int]:
        return self._dim

    def maybe_unload(self):
        if self._model is None:
            return
        idle = time.monotonic() - self._last_used_at
        if idle > self.idle_unload_secs:
            logger.info("Unloading model after %.0fs idle", idle)
            self._model = None
            # Подсказка GC: torch держит много памяти, надо явно освобождать
            import gc
            gc.collect()


_holder = _ModelHolder(MODEL_ID, IDLE_UNLOAD)


# ────────────────────────────────────────────────────────────────────
# Embedding storage helpers
# ────────────────────────────────────────────────────────────────────

def _vec_to_blob(vec) -> bytes:
    """np.ndarray (float32) → little-endian binary blob."""
    import numpy as np
    arr = vec.astype(np.float32, copy=False)
    return arr.tobytes(order="C")


def _blob_to_vec(blob: bytes):
    import numpy as np
    return np.frombuffer(blob, dtype=np.float32)


def _hash_text(title: str, content: str) -> str:
    h = hashlib.sha256()
    h.update((title or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((content or "").encode("utf-8"))
    return h.hexdigest()


# ────────────────────────────────────────────────────────────────────
# Worker loop
# ────────────────────────────────────────────────────────────────────

async def _process_outbox_batch(db, batch_size: int) -> int:
    """Обработать одну партию событий из outbox. Возвращает количество
    реально проиндексированных строк."""
    from sqlalchemy import text as sql_text
    from app.services.search_indexer import EXTRACTORS, _get_entity_class

    # Берём pending события (после flush, но возможно не доставленные
    # webhook'ом). Embedding-worker и outbox-worker НЕ конфликтуют —
    # они работают с разными вещами (outbox-worker шлёт webhook'и, мы
    # индексируем эмбеддинги). Не помечаем строку delivered.
    #
    # Логика: смотрим last_processed_event_id (хранится в текущей сессии
    # как глобальная переменная); если новый event_id появился — берём.
    # Для упрощения здесь — берём по `embedded_at IS NULL` маркеру в
    # отдельной таблице. На MVP — поллим search_embeddings и сравниваем
    # с актуальным content_hash из FTS-меты.

    # Берём строки, у которых:
    #   • embedding ещё не сгенерирован (`e.entity_id IS NULL`), ИЛИ
    #   • content_hash в FTS-мете отличается от embedding'а (поменялся текст), ИЛИ
    #   • embedding сгенерирован другой моделью (`model_name != MODEL_ID`) —
    #     это закрывает кейс миграции e5 → bge-m3 без ручной очистки таблицы.
    rows = (await db.execute(sql_text("""
        SELECT m.entity_type, m.entity_id, m.content_hash
        FROM search_index_meta m
        LEFT JOIN search_embeddings e
            ON e.entity_type = m.entity_type AND e.entity_id = m.entity_id
        WHERE e.entity_id IS NULL
           OR e.content_hash != m.content_hash
           OR e.model_name != :model
        LIMIT :lim
    """), {"lim": batch_size, "model": MODEL_ID})).all()

    if not rows:
        return 0

    # Сгребаем тексты для batched encode (одной партией быстрее на CPU).
    titles, contents, keys, hashes = [], [], [], []
    for entity_type, entity_id, content_hash in rows:
        if entity_type not in EXTRACTORS:
            continue
        entity_class = _get_entity_class(entity_type)
        if entity_class is None:
            continue
        # PK конверсия как в search_indexer (uuid-fallback)
        import uuid as _uuid
        try:
            pk_value = _uuid.UUID(str(entity_id))
        except (ValueError, AttributeError, TypeError):
            pk_value = entity_id
        try:
            entity = await db.get(entity_class, pk_value)
        except Exception:
            entity = await db.get(entity_class, entity_id)
        if entity is None:
            continue
        extracted = EXTRACTORS[entity_type](entity)
        if extracted is None:
            continue
        title, content = extracted
        # Текст для encoder'а: для bge-m3 это просто "title. content".
        # e5 ожидает префикс "passage: " — но bge-m3 нет. Выбираем
        # модель-агностичный простой формат.
        full_text = f"{title}. {content}".strip()
        if not full_text:
            continue
        titles.append(title)
        contents.append(content)
        keys.append((entity_type, str(entity_id)))
        hashes.append(content_hash)

    if not titles:
        return 0

    full_texts = [f"{t}. {c}".strip() for t, c in zip(titles, contents)]
    model = await _holder.get()

    logger.info("Embedding batch of %d items", len(full_texts))
    started = time.monotonic()
    # normalize_embeddings=True → cosine = dot product, проще считать.
    embeddings = model.encode(
        full_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=16,
    )
    elapsed = time.monotonic() - started
    logger.info("Encoded %d items in %.2fs (%.1f items/s)",
                len(full_texts), elapsed, len(full_texts) / max(elapsed, 0.001))

    # UPSERT'им (SQLite INSERT ... ON CONFLICT REPLACE)
    dim = embeddings.shape[-1]
    for (entity_type, entity_id), content_hash, vec in zip(keys, hashes, embeddings):
        blob = _vec_to_blob(vec)
        await db.execute(sql_text("""
            INSERT INTO search_embeddings
                (entity_type, entity_id, model_name, dim, embedding, content_hash, updated_at)
            VALUES (:et, :eid, :mn, :dim, :emb, :hash, CURRENT_TIMESTAMP)
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                model_name = excluded.model_name,
                dim = excluded.dim,
                embedding = excluded.embedding,
                content_hash = excluded.content_hash,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "et": entity_type, "eid": entity_id,
            "mn": MODEL_ID, "dim": dim,
            "emb": blob, "hash": content_hash,
        })
    await db.commit()
    return len(full_texts)


async def main_loop():
    from app.database.session import async_session

    logger.info("embedding_worker starting (model=%s, poll=%.1fs, idle_unload=%.0fs)",
                MODEL_ID, POLL_INTERVAL, IDLE_UNLOAD)
    total_processed = 0
    idle_ticks = 0

    while _RUNNING:
        try:
            async with async_session() as db:
                processed = await _process_outbox_batch(db, BATCH_SIZE)
            if processed > 0:
                total_processed += processed
                idle_ticks = 0
                logger.info("Processed %d (total=%d)", processed, total_processed)
            else:
                idle_ticks += 1
                if idle_ticks == 5:  # каждые ~10с idle
                    logger.debug("Idle (no pending embeddings)")
                _holder.maybe_unload()
        except Exception as exc:
            logger.exception("worker tick error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)

    logger.info("embedding_worker stopped (total processed: %d)", total_processed)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
        sys.exit(0)
