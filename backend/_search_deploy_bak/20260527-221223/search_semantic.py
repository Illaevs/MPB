"""
Step 1 поиска: семантический re-ranker для гибридного поиска.

Что делает:
  • Lazy-load embedding-модели в FastAPI-процессе (только когда первый
    запрос с включённым hybrid-режимом).
  • `embed_query(text)` — возвращает np.float32 vector.
  • `rerank_with_embeddings(query_vec, candidates)` — для списка
    кандидатов (entity_type, entity_id, bm25_score) из FTS5 подтягивает
    их embeddings из `search_embeddings` и пересчитывает финальный score
    через RRF (Reciprocal Rank Fusion) от BM25-ранга и cosine-ранга.

Memory:
  • Модель грузится один раз при первом запросе. Auto-unload через
    `EMBEDDING_IDLE_UNLOAD_SECS` (то же что у worker'а), чтобы FastAPI
    не сидел постоянно с 3 ГБ занятыми.
  • Если deps (`sentence-transformers`) не установлены или модель
    не грузится — search-router gracefully fallback'ит на FTS5-only.

Активация:
  • ENV `ENABLE_HYBRID_SEARCH=1` — иначе всегда FTS5-only.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


MODEL_ID = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
IDLE_UNLOAD = float(os.environ.get("EMBEDDING_IDLE_UNLOAD_SECS", "900"))
ENABLED = os.environ.get("ENABLE_HYBRID_SEARCH", "0") == "1"
# Минимальное количество embeddings в типе для активации hybrid для этого типа.
# Меньше — semantic будет шумным (мало точек для сравнения).
MIN_EMBEDDINGS_PER_TYPE = int(os.environ.get("HYBRID_MIN_EMBEDDINGS_PER_TYPE", "10"))


class _LazyModel:
    """Lazy-load модели в FastAPI-процессе."""

    def __init__(self):
        self._model: Optional[Any] = None
        self._dim: Optional[int] = None
        self._last_used_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self):
        async with self._lock:
            if self._model is None:
                logger.info("Loading hybrid-search model: %s", MODEL_ID)
                started = time.monotonic()
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(MODEL_ID, device="cpu")
                    # Probe dim
                    probe = self._model.encode(["probe"], normalize_embeddings=True)
                    self._dim = int(probe.shape[-1])
                except Exception as exc:
                    logger.warning(
                        "Failed to load embedding model: %s. Hybrid search will be DISABLED.",
                        exc,
                    )
                    raise
                elapsed = time.monotonic() - started
                logger.info("Hybrid model loaded (dim=%d) in %.1fs", self._dim, elapsed)
        self._last_used_at = time.monotonic()
        return self._model

    def maybe_unload(self):
        if self._model is None:
            return
        idle = time.monotonic() - self._last_used_at
        if idle > IDLE_UNLOAD:
            logger.info("Unloading hybrid model after %.0fs idle", idle)
            self._model = None
            import gc
            gc.collect()


_lazy = _LazyModel()


# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────

def is_hybrid_enabled() -> bool:
    """ENV-флаг + deps доступны. Можно вызывать без try/except."""
    if not ENABLED:
        return False
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


async def embed_query(text: str):
    """Embed строку запроса. None если что-то пошло не так."""
    try:
        model = await _lazy.get()
        vec = model.encode([text], normalize_embeddings=True)[0]
        return vec
    except Exception as exc:
        logger.warning("embed_query failed: %s", exc)
        return None


def _blob_to_vec(blob: bytes):
    return np.frombuffer(blob, dtype=np.float32)


async def _types_with_embeddings(
    db: AsyncSession, entity_types: List[str]
) -> Dict[str, int]:
    """Для каких типов уже накоплено >= MIN_EMBEDDINGS_PER_TYPE строк
    СОВПАДАЮЩЕЙ модели. При смене EMBEDDING_MODEL старые embeddings
    другой размерности игнорируются (cosine между разными dim бы упал)."""
    if not entity_types:
        return {}
    placeholders = ",".join([f":t{i}" for i in range(len(entity_types))])
    params: Dict[str, Any] = {f"t{i}": et for i, et in enumerate(entity_types)}
    params["model"] = MODEL_ID
    rows = (await db.execute(sql_text(f"""
        SELECT entity_type, COUNT(*) AS cnt
        FROM search_embeddings
        WHERE entity_type IN ({placeholders})
          AND model_name = :model
        GROUP BY entity_type
    """), params)).all()
    return {r[0]: int(r[1]) for r in rows}


async def semantic_candidates(
    db: AsyncSession,
    query_vec,
    entity_types: List[str],
    limit: int = 200,
) -> List[Tuple[str, str, float]]:
    """Получить top-N кандидатов чисто по cosine similarity, БЕЗ FTS5.

    Это альтернативный путь отбора: запрос → embedding → cosine со всеми
    embeddings → top-N. Нужен для запросов где лексических совпадений
    нет («аудит и ревью» vs «проверить разделы»), а семантика — есть.

    Возвращает [(entity_type, entity_id, cosine_score)] sorted desc.
    Brute-force через NumPy. Для <100k embeddings — мгновенно.
    Когда подключим sqlite-vec extension — заменим на ANN-индекс.
    """
    if not entity_types or query_vec is None:
        return []

    placeholders = ",".join([f":t{i}" for i in range(len(entity_types))])
    params: Dict[str, Any] = {f"t{i}": et for i, et in enumerate(entity_types)}
    params["model"] = MODEL_ID

    rows = (await db.execute(sql_text(f"""
        SELECT entity_type, entity_id, embedding
        FROM search_embeddings
        WHERE entity_type IN ({placeholders})
          AND model_name = :model
    """), params)).all()

    if not rows:
        return []

    qv = np.asarray(query_vec, dtype=np.float32)
    scored: List[Tuple[str, str, float]] = []
    for et, eid, blob in rows:
        vec = np.frombuffer(blob, dtype=np.float32)
        if vec.size == 0 or vec.size != qv.size:
            continue
        # Embeddings уже normalize'нуты → dot = cosine
        scored.append((et, eid, float(np.dot(qv, vec))))

    scored.sort(key=lambda x: -x[2])
    return scored[:limit]


async def rerank_with_embeddings(
    db: AsyncSession,
    query_vec,
    candidates: List[Tuple[str, str, float]],  # (entity_type, entity_id, bm25_score)
    k_rrf: int = 60,
) -> List[Tuple[str, str, float]]:
    """RRF-объединение BM25-рангов и cosine-рангов.

    RRF: для каждого документа `final_score = sum(1 / (k + rank_i))`
    где rank_i — позиция документа в каждом из источников рейтинга.
    Этот метод устойчив к разным шкалам score'ов (BM25 — отрицательный,
    cosine — [-1, 1]).

    Параметры:
      candidates — top-N из FTS5 уже отсортированный (BM25 ASC = более релевантно).
      query_vec — embedding запроса (np.float32).
      k_rrf — параметр RRF (по умолчанию 60, стандарт из литературы).

    Возвращает список тех же кандидатов в новом порядке, где score —
    финальный RRF.
    """
    if not candidates or query_vec is None:
        return candidates

    # Подтягиваем embeddings для всех кандидатов одним запросом.
    # ВАЖНО: фильтр `model_name = MODEL_ID` — иначе при смене модели
    # размерность не совпадёт с qv и np.dot бросит ValueError.
    keys = [(c[0], c[1]) for c in candidates]
    if not keys:
        return candidates
    or_clauses = []
    params: Dict[str, Any] = {"model": MODEL_ID}
    for i, (et, eid) in enumerate(keys):
        or_clauses.append(f"(entity_type = :et{i} AND entity_id = :eid{i})")
        params[f"et{i}"] = et
        params[f"eid{i}"] = eid
    rows = (await db.execute(sql_text(f"""
        SELECT entity_type, entity_id, embedding
        FROM search_embeddings
        WHERE ({' OR '.join(or_clauses)})
          AND model_name = :model
    """), params)).all()

    embeddings_map = {(r[0], r[1]): _blob_to_vec(r[2]) for r in rows}

    # Считаем cosine для тех кандидатов, у кого есть embedding.
    cosine_scores = []
    qv = np.asarray(query_vec, dtype=np.float32)
    for et, eid, _bm25 in candidates:
        vec = embeddings_map.get((et, eid))
        if vec is None or vec.size == 0 or qv.size == 0:
            cosine_scores.append(((et, eid), -1.0))
        else:
            # Embeddings уже normalize'нуты → dot = cosine.
            score = float(np.dot(qv, vec))
            cosine_scores.append(((et, eid), score))

    # Ранги в каждом источнике (1-based).
    bm25_rank = {(c[0], c[1]): i + 1 for i, c in enumerate(candidates)}
    cosine_rank = {
        (et_eid[0], et_eid[1]): i + 1
        for i, (et_eid, _) in enumerate(sorted(cosine_scores, key=lambda x: -x[1]))
    }

    # RRF.
    rrf_scores: List[Tuple[str, str, float]] = []
    for et, eid, _bm25 in candidates:
        r_bm25 = bm25_rank.get((et, eid), len(candidates) + 1)
        r_cos = cosine_rank.get((et, eid), len(candidates) + 1)
        rrf = 1.0 / (k_rrf + r_bm25) + 1.0 / (k_rrf + r_cos)
        rrf_scores.append((et, eid, rrf))

    # Возвращаем отсортированный по RRF DESC.
    rrf_scores.sort(key=lambda x: -x[2])
    return rrf_scores
