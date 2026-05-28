"""
Reglaments Phase 0: API для нормативной базы (СНиП/ГОСТ/СП/ФЗ).

ИЗОЛИРОВАННЫЙ домен от основного `/api/v1/search`. Свой FTS5 индекс
(`reglament_fts`), свои embeddings (`reglament_embeddings`), своя
ранжировка. Не пересекается с deals/tasks/companies.

Endpoints:
  GET  /                         — список норм (фильтры по doc_type/status/discipline)
  GET  /{id}                     — детальный документ с оглавлением
  GET  /{id}/sections/{sid}      — отдельная секция (для прямой ссылки)
  POST /search                   — поиск по нормам (BM25 + cosine RRF)
  POST /upload                   — admin: загрузка новой нормы (Phase 3, заглушка)
  POST /{id}/reindex             — admin: переиндексация (Phase 3, заглушка)

Доступ:
  • Чтение (GET, /search) — любой авторизованный (нормы — общесправочник).
  • Запись (upload, reindex, DELETE) — только superadmin.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, text, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Reglament, ReglamentSection, User
from app.services.search_semantic import (
    is_hybrid_enabled,
    embed_query,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────────────────────────────────────────────────
# Pydantic схемы
# ────────────────────────────────────────────────────────────────────

class ReglamentBrief(BaseModel):
    """Краткое описание нормы для списка/каталога."""
    id: str
    doc_type: str
    doc_number: str
    title: str
    status: str
    discipline_tags: Optional[str] = None
    effective_date: Optional[str] = None
    section_count: int = 0


class ReglamentSectionBrief(BaseModel):
    """Секция нормы — для оглавления и результата поиска."""
    id: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    order_idx: int = 0
    char_count: int = 0
    # Контент НЕ возвращаем в списке секций — отдельным запросом.


class ReglamentDetail(BaseModel):
    """Полный документ с оглавлением (контент секций — по запросу)."""
    id: str
    doc_type: str
    doc_number: str
    title: str
    full_title: Optional[str] = None
    status: str
    effective_date: Optional[str] = None
    cancelled_date: Optional[str] = None
    replaced_by_id: Optional[str] = None
    discipline_tags: Optional[str] = None
    source_url: Optional[str] = None
    page_count: Optional[int] = None
    section_count: int = 0
    sections: List[ReglamentSectionBrief] = Field(default_factory=list)


class ReglamentSectionFull(BaseModel):
    """Полная секция с контентом."""
    id: str
    reglament_id: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    content: str
    parent_section_id: Optional[str] = None
    order_idx: int = 0
    # Контекст родительского документа для UI-breadcrumb.
    reglament_doc_number: Optional[str] = None
    reglament_doc_type: Optional[str] = None
    reglament_title: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    # Опциональные фильтры (если не указаны — ищем по всему).
    doc_types: Optional[List[str]] = None  # ['СП', 'ГОСТ']
    statuses: Optional[List[str]] = None   # ['actual']
    disciplines: Optional[List[str]] = None  # ['КЖ', 'КМ']


class SearchHit(BaseModel):
    section_id: str
    reglament_id: str
    doc_type: str
    doc_number: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    snippet: str
    reglament_title: str
    score: float = 0.0


class SearchResponse(BaseModel):
    items: List[SearchHit]
    total: int
    query: str
    mode: str = "fts"  # "fts" / "hybrid"


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

_FTS_SAFE = re.compile(r"[^\w\sа-яА-ЯёЁ\-\.]", re.UNICODE)


def _sanitize_fts_query(q: str) -> str:
    """Чистим FTS5-запрос + лёгкая морфологическая нормализация для
    русского текста.

    Проблема: FTS5 tokenizer `unicode61` не стеммит. В нормах везде
    «арматуры», «бетонные», «защитного» — но пользователь печатает
    «арматура», «бетонный», «защитный». Без обработки prefix-match
    `арматура*` НЕ матчит «арматуры» (отличается последней буквой).

    Решение — дешёвый стеммер: обрезаем последнюю букву у слова длиной
    ≥4 символов и применяем prefix. «арматура» → `арматур*` → матчит
    арматура, арматуры, арматурой, арматурам и т.д. Короткие слова
    (≤3 букв: «СП», «РФ») оставляем exact-match.

    Для production-качества нужен pymorphy3 (lemma → prefix), но для
    Phase 0 эвристики достаточно.
    """
    q = (q or "").strip()
    if not q:
        return ""
    q = _FTS_SAFE.sub(" ", q)
    tokens = [t for t in q.split() if t]
    if not tokens:
        return ""

    out: List[str] = []
    for t in tokens:
        # Удаляем ведущие/завершающие дефисы — FTS5 трактует `-` как NOT.
        t = t.strip("-")
        if not t:
            continue
        if len(t) >= 7:
            # Длинные слова — обрезаем 2 буквы (агрессивная → агрессив*,
            # защитный → защитн*, долговечность → долговечнос*).
            out.append(t[:-2] + "*")
        elif len(t) >= 4:
            # Средние — обрезаем 1 букву (бетон → бето*, среда → сред*).
            out.append(t[:-1] + "*")
        else:
            # Короткие токены — exact (СП, РФ, ГОСТ-Р…).
            out.append(t)
    return " ".join(out)


# ────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ReglamentBrief])
async def list_reglaments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    discipline: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Каталог нормативной базы с фильтрами.

    Поиск (`q`) — простой LIKE по doc_number/title. Семантический поиск —
    через POST /search.
    """
    stmt = select(Reglament)
    if doc_type:
        stmt = stmt.where(Reglament.doc_type == doc_type)
    if status:
        stmt = stmt.where(Reglament.status == status)
    if discipline:
        # Дисциплины — CSV: ищем "КЖ" в "КЖ,КМ,АР".
        stmt = stmt.where(Reglament.discipline_tags.like(f"%{discipline}%"))
    if q:
        q_like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            Reglament.doc_number.like(q_like),
            Reglament.title.like(q_like),
            Reglament.full_title.like(q_like),
        ))
    stmt = stmt.order_by(Reglament.doc_type, Reglament.doc_number).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        ReglamentBrief(
            id=str(r.id),
            doc_type=r.doc_type,
            doc_number=r.doc_number,
            title=r.title,
            status=r.status,
            discipline_tags=r.discipline_tags,
            effective_date=r.effective_date.isoformat() if r.effective_date else None,
            section_count=r.section_count or 0,
        )
        for r in rows
    ]


@router.get("/{reglament_id}", response_model=ReglamentDetail)
async def get_reglament(
    reglament_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Документ + оглавление (секции без контента — экономим payload)."""
    r = (await db.execute(
        select(Reglament).where(Reglament.id == reglament_id)
    )).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="Норма не найдена")

    sections = (await db.execute(
        select(ReglamentSection)
        .where(ReglamentSection.reglament_id == reglament_id)
        .order_by(ReglamentSection.order_idx)
    )).scalars().all()

    return ReglamentDetail(
        id=str(r.id),
        doc_type=r.doc_type,
        doc_number=r.doc_number,
        title=r.title,
        full_title=r.full_title,
        status=r.status,
        effective_date=r.effective_date.isoformat() if r.effective_date else None,
        cancelled_date=r.cancelled_date.isoformat() if r.cancelled_date else None,
        replaced_by_id=str(r.replaced_by_id) if r.replaced_by_id else None,
        discipline_tags=r.discipline_tags,
        source_url=r.source_url,
        page_count=r.page_count,
        section_count=r.section_count or 0,
        sections=[
            ReglamentSectionBrief(
                id=str(s.id),
                section_number=s.section_number,
                section_title=s.section_title,
                order_idx=s.order_idx,
                char_count=s.char_count or 0,
            )
            for s in sections
        ],
    )


@router.get("/sections/{section_id}", response_model=ReglamentSectionFull)
async def get_section(
    section_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Полный текст конкретной секции (для прямой ссылки из поиска или
    другого места системы)."""
    row = (await db.execute(text("""
        SELECT
            s.id, s.reglament_id, s.section_number, s.section_title,
            s.content, s.parent_section_id, s.order_idx,
            r.doc_number, r.doc_type, r.title
        FROM reglament_sections s
        JOIN reglaments r ON r.id = s.reglament_id
        WHERE s.id = :id
    """), {"id": section_id})).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Раздел не найден")

    return ReglamentSectionFull(
        id=str(row[0]),
        reglament_id=str(row[1]),
        section_number=row[2],
        section_title=row[3],
        content=row[4],
        parent_section_id=str(row[5]) if row[5] else None,
        order_idx=int(row[6]),
        reglament_doc_number=row[7],
        reglament_doc_type=row[8],
        reglament_title=row[9],
    )


@router.post("/search", response_model=SearchResponse)
async def search_reglaments(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Полнотекстовый + семантический поиск по нормативной базе.

    Тот же паттерн что в `routers/search.py`: FTS5 BM25 + cosine top-N
    через bge-m3, объединение через RRF. Но СВОЙ индекс
    (`reglament_fts` / `reglament_embeddings`) — не пересекается с
    основным CRM-поиском.
    """
    fts_query = _sanitize_fts_query(payload.query)
    if not fts_query:
        return SearchResponse(items=[], total=0, query=payload.query, mode="fts")

    # 1. Hybrid активен только если есть embeddings ХОТЯ БЫ для одного
    # документа — иначе чистый FTS5.
    hybrid_active = False
    if is_hybrid_enabled():
        cnt = (await db.execute(text(
            "SELECT COUNT(*) FROM reglament_embeddings"
        ))).scalar() or 0
        hybrid_active = cnt > 0

    # 2. Базовый отбор через FTS5 BM25.
    candidate_limit = 200 if hybrid_active else (payload.limit + 50)

    # Фильтры по doc_type/status/discipline применяются через JOIN с reglaments.
    where_clauses = ["fts.reglament_fts MATCH :q"]
    params: Dict[str, Any] = {"q": fts_query, "lim": candidate_limit, "off": payload.offset}

    if payload.doc_types:
        dt_placeholders = ",".join([f":dt{i}" for i in range(len(payload.doc_types))])
        where_clauses.append(f"r.doc_type IN ({dt_placeholders})")
        for i, dt in enumerate(payload.doc_types):
            params[f"dt{i}"] = dt

    if payload.statuses:
        st_placeholders = ",".join([f":st{i}" for i in range(len(payload.statuses))])
        where_clauses.append(f"r.status IN ({st_placeholders})")
        for i, st in enumerate(payload.statuses):
            params[f"st{i}"] = st

    if payload.disciplines:
        # CSV-фильтр: одна дисциплина → r.discipline_tags LIKE '%X%'
        # несколько → OR
        d_clauses = []
        for i, d in enumerate(payload.disciplines):
            d_clauses.append(f"r.discipline_tags LIKE :d{i}")
            params[f"d{i}"] = f"%{d}%"
        where_clauses.append("(" + " OR ".join(d_clauses) + ")")

    where_sql = " AND ".join(where_clauses)

    fts_sql = f"""
        SELECT
            fts.section_id,
            fts.reglament_id,
            r.doc_type,
            r.doc_number,
            r.title,
            fts.section_number,
            fts.section_title,
            snippet(reglament_fts, 6, '<mark>', '</mark>', '…', 16) AS snippet,
            bm25(reglament_fts, 1.0, 1.0, 2.0, 1.5, 1.0) AS score
        FROM reglament_fts fts
        JOIN reglaments r ON r.id = fts.reglament_id
        WHERE {where_sql}
        ORDER BY score ASC
        LIMIT :lim OFFSET :off
    """
    fts_rows = (await db.execute(text(fts_sql), params)).all()

    if not hybrid_active:
        # FTS-only — возвращаем что нашли.
        items = [
            SearchHit(
                section_id=str(r[0]),
                reglament_id=str(r[1]),
                doc_type=r[2],
                doc_number=r[3],
                reglament_title=r[4],
                section_number=r[5],
                section_title=r[6],
                snippet=r[7] or "",
                score=float(r[8] or 0),
            )
            for r in fts_rows[: payload.limit]
        ]
        return SearchResponse(
            items=items,
            total=len(items),
            query=payload.query,
            mode="fts",
        )

    # 3. Hybrid — добавляем pure-semantic ветку.
    import numpy as np
    query_vec = await embed_query(payload.query)
    sem_candidates: List[tuple] = []
    if query_vec is not None:
        # Pure-semantic: cosine со всеми reglament_embeddings.
        # Brute-force NumPy. Для <100k записей — OK; для больше — нужен
        # sqlite-vec ANN (Phase 4).
        sem_rows = (await db.execute(text(
            "SELECT section_id, reglament_id, embedding FROM reglament_embeddings"
        ))).all()
        qv = np.asarray(query_vec, dtype=np.float32)
        scored: List[tuple] = []
        for sid, rid, blob in sem_rows:
            vec = np.frombuffer(blob, dtype=np.float32)
            if vec.size == 0 or vec.size != qv.size:
                continue
            cos = float(np.dot(qv, vec))
            scored.append((sid, rid, cos))
        scored.sort(key=lambda x: -x[2])
        # Минимальный порог cosine — отсекаем шум (как в основном поиске).
        from app.services.search_semantic import MIN_COSINE
        sem_candidates = [c for c in scored if c[2] >= MIN_COSINE][:candidate_limit]

    # 4. RRF — объединяем ранги FTS и semantic.
    K_RRF = 60
    fts_rank = {str(r[0]): i + 1 for i, r in enumerate(fts_rows)}
    sem_rank = {str(c[0]): i + 1 for i, c in enumerate(sem_candidates)}
    all_keys = set(fts_rank.keys()) | set(sem_rank.keys())

    rrf_scored: List[tuple] = []
    for key in all_keys:
        r_fts = fts_rank.get(key, len(fts_rows) + 1)
        r_sem = sem_rank.get(key, len(sem_candidates) + 1)
        rrf = 1.0 / (K_RRF + r_fts) + 1.0 / (K_RRF + r_sem)
        rrf_scored.append((key, rrf))
    rrf_scored.sort(key=lambda x: -x[1])

    # 5. Подтягиваем метаданные для всех ключей (для FTS уже есть,
    # для semantic-only — отдельный SELECT).
    fts_index = {str(r[0]): r for r in fts_rows}
    missing = [k for k, _ in rrf_scored if k not in fts_index]
    if missing:
        placeholders = ",".join([f":s{i}" for i in range(len(missing))])
        extra_params = {f"s{i}": v for i, v in enumerate(missing)}
        extra_rows = (await db.execute(text(f"""
            SELECT
                s.id, s.reglament_id, r.doc_type, r.doc_number, r.title,
                s.section_number, s.section_title, substr(s.content, 1, 200)
            FROM reglament_sections s
            JOIN reglaments r ON r.id = s.reglament_id
            WHERE s.id IN ({placeholders})
        """), extra_params)).all()
        for er in extra_rows:
            fts_index[str(er[0])] = (
                er[0], er[1], er[2], er[3], er[4], er[5], er[6],
                (er[7] or "") + "…", 0.0,
            )

    items: List[SearchHit] = []
    for key, rrf in rrf_scored:
        orig = fts_index.get(key)
        if orig is None:
            continue
        items.append(SearchHit(
            section_id=str(orig[0]),
            reglament_id=str(orig[1]),
            doc_type=orig[2],
            doc_number=orig[3],
            reglament_title=orig[4],
            section_number=orig[5],
            section_title=orig[6],
            snippet=orig[7] or "",
            score=rrf,
        ))
        if len(items) >= payload.limit:
            break

    return SearchResponse(
        items=items,
        total=len(items),
        query=payload.query,
        mode="hybrid",
    )
