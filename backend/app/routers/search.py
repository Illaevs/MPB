"""
Step 0+1 поиска: POST /api/v1/search — полнотекстовый поиск.

Архитектура (двухрежимная):
  • **Step 0 (FTS5-only):** запрос → FTS5 MATCH с BM25 ранжированием.
    Title-колонка boost'нута через columnsweight (`bm25(search_fts, 3.0, 1.0)`).
    Работает всегда, не требует embedding-worker'а.
  • **Step 1 (hybrid):** дополнительно использует cosine similarity
    между embedding(query) и embeddings(candidates) из `search_embeddings`,
    объединяет с BM25 через RRF (Reciprocal Rank Fusion). Активируется
    автоматически если в `search_embeddings` есть строки для нужных
    entity_types (порог: >=10 эмбеддингов в типе).

ACL:
  • Для каждого `entity_type` применяется секционный фильтр
    (`read_all` / `read_assigned` через `get_section_permissions`).
    Если у юзера нет даже read_assigned для секции — результаты этого
    типа полностью скрыты.
  • Per-row ACL (assigned-only): мы джойним results к источнику-таблице
    и проверяем, видит ли юзер конкретную запись (assigned_to_user_id,
    created_by, watcher list и т.п.).

Snippet: FTS5 функция `snippet(...)` подсвечивает совпадения через
`<mark>...</mark>` (фронт уже умеет рендерить).

Пагинация: limit/offset.

Не поддерживаем (по дизайну):
  • Boolean-операторы (FTS5-синтаксис AND/OR) — пока экранируем
    спецсимволы.
  • Filter по полю payload — FTS5 не индексирует payload.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import User
from app.services.permissions import get_section_permissions
from app.services.search_semantic import (
    is_hybrid_enabled,
    embed_query,
    rerank_with_embeddings,
    semantic_candidates,
    _types_with_embeddings,
    MIN_EMBEDDINGS_PER_TYPE,
    MIN_COSINE,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────────────────────────────────────────────────
# Маппинг entity_type → (section_key, source_table, owner_col, assigned_col)
#
# section_key: ключ секции в системе прав (`get_section_permissions`)
# source_table: таблица в БД, в которую идёт JOIN для per-row ACL
# owner_col / assigned_col: колонки для проверки прав в режиме read_assigned
#   (если оба None — режим read_assigned не поддерживается, нужен read_all)
# ────────────────────────────────────────────────────────────────────

ENTITY_ACL_MAP: Dict[str, Dict[str, Optional[str]]] = {
    "deal": {
        "section": "projects",
        "table": "deals",
        # для deals нет одного owner_col — используем deal_gips link table.
        # В простом MVP: read_assigned == read_all для текущего юзера,
        # так как deals не имеют прямой owner-колонки. Можно уточнить.
        "owner_col": None,
        "assigned_col": None,
    },
    "contract": {"section": "contracts", "table": "contracts", "owner_col": None, "assigned_col": None},
    "lead": {
        "section": "leads",
        "table": "leads",
        # У модели Lead единственная user-колонка — responsible_user_id.
        # Колонок created_by_user_id / assigned_to_user_id НЕТ
        # (модель: backend/app/models/lead.py). Используем её
        # как owner_col, assigned_col оставляем пустым.
        "owner_col": "responsible_user_id",
        "assigned_col": None,
    },
    "company": {"section": "companies", "table": "companies", "owner_col": None, "assigned_col": None},
    "task": {
        "section": "tasks",
        "table": "tasks",
        "owner_col": "created_by_user_id",
        "assigned_col": "assigned_to_user_id",
    },
    "document": {"section": "document_registry", "table": "documents", "owner_col": None, "assigned_col": None},
    "outgoing_document": {
        "section": "outgoing_registry",
        "table": "outgoing_documents",
        # owner_col намеренно None: в модели OutgoingDocument нет
        # created_by_user_id, поэтому assigned-режим в section_modes
        # для них не работает. Per-row фильтр на эту сущность —
        # через JOIN с deal_id ниже в block per-row ACL.
        "owner_col": None,
        "assigned_col": None,
    },
    "kp_document": {"section": "leads", "table": "kp_documents", "owner_col": None, "assigned_col": None},
    "mail_message": {"section": "mail", "table": "mail_messages", "owner_col": None, "assigned_col": None},
    "legal_case": {"section": "legal_work", "table": "legal_cases", "owner_col": None, "assigned_col": None},
    "support_ticket": {"section": "support", "table": "support_tickets", "owner_col": None, "assigned_col": None},
    "task_message": {"section": "task_chat", "table": "task_messages", "owner_col": "user_id", "assigned_col": None},
    "task_subtask": {"section": "tasks", "table": "task_subtasks", "owner_col": "created_by_user_id", "assigned_col": "assigned_to_user_id"},
    "subcontractor_card": {"section": "contracts", "table": "subcontractor_cards", "owner_col": None, "assigned_col": None},
}


# ────────────────────────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    entity_types: Optional[List[str]] = Field(None, description="Ограничить типы; null = все доступные")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str
    score: float
    # parent_id — для дочерних сущностей (task_message → task_id,
    # task_subtask → task_id). Фронту нужно чтобы при клике открыть
    # родительскую сущность (модал задачи), а не саму запись.
    parent_id: Optional[str] = None
    parent_type: Optional[str] = None


class SearchResponse(BaseModel):
    items: List[SearchHit]
    total: int
    query: str
    mode: str = "fts"  # "fts" | "hybrid"


# ────────────────────────────────────────────────────────────────────
# FTS5 query sanitization
# ────────────────────────────────────────────────────────────────────

def _sanitize_fts_query(raw: str) -> str:
    """Очищаем запрос от FTS5-спецсимволов и оборачиваем токены в кавычки.

    FTS5-операторы (AND / OR / NEAR / -term / "term") — выключаем,
    чтобы случайный дефис или кавычка пользователя не сломали SQL.

    Логика:
      • Разбиваем по пробелам.
      • Каждый токен >1 символ оборачиваем в "..." (FTS5 trigger phrase
        match) + добавляем `*` для prefix matching.
      • Соединяем через пробел (= неявный AND в FTS5).

    Examples:
      "бетон м300"   → '"бетон"* "м300"*'
      "ООО Ромашка"  → '"ООО"* "Ромашка"*'
      "tel: 8-800"   → '"tel"* "8"* "800"*'  (двоеточие и дефис убраны)
    """
    if not raw or not raw.strip():
        return ""
    # Удаляем FTS5-спецсимволы из каждого токена.
    cleaned = re.sub(r'[\^\(\)\"\\:\-\+]', " ", raw)
    tokens = [t for t in cleaned.split() if len(t) >= 1]
    if not tokens:
        return ""
    # Лимит на запрос: не больше 10 токенов (защита от DoS).
    tokens = tokens[:10]
    parts = [f'"{t}"*' for t in tokens]
    return " ".join(parts)


# ────────────────────────────────────────────────────────────────────
# Endpoint
# ────────────────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Полнотекстовый поиск по сущностям CRM.

    Применяет per-section ACL: пользователь не увидит результатов
    из секций, к которым у него нет даже `read_assigned`. Для
    режима `read_assigned` дополнительно фильтруем по owner_col /
    assigned_col источника-таблицы.
    """
    fts_query = _sanitize_fts_query(payload.query)
    if not fts_query:
        return SearchResponse(items=[], total=0, query=payload.query, mode="fts")

    # 1. Резолвим доступные типы.
    requested_types = payload.entity_types or list(ENTITY_ACL_MAP.keys())
    allowed_types: List[str] = []
    section_modes: Dict[str, str] = {}  # entity_type → "all" / "assigned"

    for et in requested_types:
        acl_info = ENTITY_ACL_MAP.get(et)
        if not acl_info:
            continue
        section = acl_info["section"]
        read_all, read_assigned = await get_section_permissions(db, user.role_id, section)
        if read_all:
            allowed_types.append(et)
            section_modes[et] = "all"
        elif read_assigned and (acl_info["owner_col"] or acl_info["assigned_col"]):
            allowed_types.append(et)
            section_modes[et] = "assigned"
        # else: skip — нет прав на секцию или нельзя сузить до assigned

    if not allowed_types:
        return SearchResponse(items=[], total=0, query=payload.query, mode="fts")

    # 1.5 Решаем включать ли hybrid для этого запроса. Активируется только
    # если ENV ENABLE_HYBRID_SEARCH=1 + deps установлены + накоплено
    # >= MIN_EMBEDDINGS_PER_TYPE эмбеддингов хотя бы для одного из
    # запрашиваемых типов.
    hybrid_active = False
    types_with_emb: Dict[str, int] = {}
    if is_hybrid_enabled():
        types_with_emb = await _types_with_embeddings(db, allowed_types)
        # активен если есть хотя бы один тип с порогом
        hybrid_active = any(cnt >= MIN_EMBEDDINGS_PER_TYPE for cnt in types_with_emb.values())

    # 2. Базовый отбор кандидатов через FTS5 (BM25).
    placeholders = ",".join([f":t{i}" for i in range(len(allowed_types))])
    type_params = {f"t{i}": et for i, et in enumerate(allowed_types)}

    # Для hybrid берём больше кандидатов — будем объединять с semantic top-N.
    candidate_limit = 200 if hybrid_active else (payload.limit + 50)
    fts_sql = f"""
        SELECT
            entity_type, entity_id, title,
            snippet(search_fts, 3, '<mark>', '</mark>', '…', 12) AS snippet,
            bm25(search_fts, 3.0, 1.0) AS score
        FROM search_fts
        WHERE search_fts MATCH :q
          AND entity_type IN ({placeholders})
        ORDER BY score ASC
        LIMIT :lim OFFSET :off
    """
    params = {"q": fts_query, "lim": candidate_limit, "off": payload.offset, **type_params}
    fts_rows = (await db.execute(text(fts_sql), params)).all()

    if not hybrid_active:
        # FTS5-only mode: ничего больше не делаем.
        rows = fts_rows
    else:
        # Hybrid: ДВУХПУТЕВОЙ retrieval.
        #   path A — FTS5 BM25 (lexical, уже получено в fts_rows)
        #   path B — pure cosine top-N (semantic)
        #   union обоих → RRF over ranks → итоговый порядок.
        # Это закрывает кейс «аудит и ревью» → находим «проверить разделы СПС»:
        # BM25 даст 0, но cosine увидит семантическую близость.
        query_vec = await embed_query(payload.query)
        sem_candidates = []
        if query_vec is not None:
            sem_candidates = await semantic_candidates(
                db, query_vec, allowed_types, limit=candidate_limit,
            )
            # Отсекаем семантический шум: на малых корпусах semantic возвращает
            # весь индекс (мест в top-N больше чем документов), и в RRF попадают
            # документы с cosine ≈ 0.1, которые ни лексически, ни семантически
            # не релевантны. Фильтр по MIN_COSINE удаляет такой хвост, оставляя
            # только реально близкие. См. HYBRID_MIN_COSINE в search_semantic.py.
            sem_candidates = [c for c in sem_candidates if c[2] >= MIN_COSINE]

        # Ранги в каждом источнике (1-based; чем меньше, тем релевантнее).
        K_RRF = 60
        fts_rank = {(r[0], r[1]): i + 1 for i, r in enumerate(fts_rows)}
        sem_rank = {(c[0], c[1]): i + 1 for i, c in enumerate(sem_candidates)}
        all_keys = set(fts_rank.keys()) | set(sem_rank.keys())

        # RRF (Reciprocal Rank Fusion).
        scored: List[tuple] = []
        for key in all_keys:
            r_fts = fts_rank.get(key, len(fts_rows) + 1)
            r_sem = sem_rank.get(key, len(sem_candidates) + 1)
            rrf = 1.0 / (K_RRF + r_fts) + 1.0 / (K_RRF + r_sem)
            scored.append((key, rrf))
        scored.sort(key=lambda x: -x[1])

        # Подтянем title/snippet/payload:
        #  • для FTS5-кандидатов уже есть в fts_rows (со snippet'ом)
        #  • для pure-semantic кандидатов (нет в FTS) — отдельный SELECT
        #    из search_fts по (entity_type, entity_id) без MATCH.
        fts_index = {(r[0], r[1]): r for r in fts_rows}
        missing_keys = [k for k, _ in scored if k not in fts_index]
        if missing_keys:
            or_clauses = []
            extra_params: Dict[str, Any] = {}
            for i, (et, eid) in enumerate(missing_keys):
                or_clauses.append(f"(entity_type = :met{i} AND entity_id = :meid{i})")
                extra_params[f"met{i}"] = et
                extra_params[f"meid{i}"] = eid
            extra_rows = (await db.execute(text(f"""
                SELECT entity_type, entity_id, title, content
                FROM search_fts
                WHERE {' OR '.join(or_clauses)}
            """), extra_params)).all()
            # Для не-FTS hit'ов snippet'а нет (snippet требует MATCH).
            # Делаем простую обрезку content до 120 символов.
            for er in extra_rows:
                content_preview = (er[3] or "")[:120]
                fts_index[(er[0], er[1])] = (er[0], er[1], er[2] or "", content_preview, 0.0)

        # Собираем финальный список (entity_type, entity_id, title, snippet, score=rrf).
        rows = []
        for key, rrf in scored:
            orig = fts_index.get(key)
            if orig is None:
                continue
            rows.append((orig[0], orig[1], orig[2], orig[3], rrf))

    # 3. Per-row ACL filtering.
    #
    # Child-entity special case: ряд сущностей имеют свою формальную
    # section в ENTITY_ACL_MAP, но реальные права завязаны на parent
    # из другой section. Без явного per-row фильтра юзер с read_all
    # на child-section увидит данные из чужих parent'ов через поиск,
    # хотя через прямой роутер (list/get) — не увидит:
    #
    #   • task_message / task_subtask → parent = task (section tasks)
    #   • outgoing_document            → parent = deal (section projects)
    #   • document                     → parent = deal (section projects)
    #   • kp_document                  → parent = lead (section leads)
    #   • support_ticket               → owner  = created_by_id (заявитель)
    #
    # Для каждого случая ниже резолвим разрешённые parent-id'ы один раз
    # перед циклом и используем для row-check без N+1.
    filtered: List[SearchHit] = []
    user_id_str = str(user.id)
    is_superuser = bool(getattr(user, "is_superuser", False))

    # Резолвим *.read_all один раз (нужно для child-entity gate).
    async def _read_all(section_key: str) -> bool:
        if is_superuser:
            return True
        ra, _ = await get_section_permissions(db, user.role_id, section_key)
        return bool(ra)

    tasks_read_all = await _read_all("tasks")
    projects_read_all = await _read_all("projects")
    leads_read_all = await _read_all("leads")
    support_read_all = await _read_all("support")

    # Резолвим allowed sets для child-entity row-check.
    # None означает «нет фильтра» (читай — у юзера read_all).
    allowed_deals: Optional[set] = None
    if not projects_read_all:
        # Юзер видит сделки где он в deal_gips ИЛИ where deal.assigned_to_user_id = u.
        # Сейчас в deals нет колонки assigned_to_user_id; пользуемся deal_gips.
        rows_d = (await db.execute(text(
            "SELECT deal_id FROM deal_gips WHERE user_id = :u"
        ), {"u": user_id_str})).fetchall()
        allowed_deals = {str(r[0]) for r in rows_d}

    allowed_leads: Optional[set] = None
    if not leads_read_all:
        # NB: в leads нет created_by/assigned_to колонок — только
        # responsible_user_id (см. app/models/lead.py).
        rows_l = (await db.execute(text(
            "SELECT id FROM leads WHERE responsible_user_id = :u"
        ), {"u": user_id_str})).fetchall()
        allowed_leads = {str(r[0]) for r in rows_l}

    # Подгружаем parent_id для child-сущностей одним SELECT'ом на тип.
    out_to_deal: Dict[str, Optional[str]] = {}
    doc_to_deal: Dict[str, Optional[str]] = {}
    kp_to_lead: Dict[str, Optional[str]] = {}
    sup_to_creator: Dict[str, Optional[str]] = {}

    def _ids_of(et: str) -> List[str]:
        return [str(r[1]) for r in rows if r[0] == et]

    if not projects_read_all:
        oids = _ids_of("outgoing_document")
        if oids:
            placeholders = ",".join([f":i{i}" for i in range(len(oids))])
            params = {f"i{i}": v for i, v in enumerate(oids)}
            for r in (await db.execute(text(
                f"SELECT id, deal_id FROM outgoing_documents WHERE id IN ({placeholders})"
            ), params)).fetchall():
                out_to_deal[str(r[0])] = str(r[1]) if r[1] else None
        dids = _ids_of("document")
        if dids:
            placeholders = ",".join([f":i{i}" for i in range(len(dids))])
            params = {f"i{i}": v for i, v in enumerate(dids)}
            for r in (await db.execute(text(
                f"SELECT id, project_id FROM documents WHERE id IN ({placeholders})"
            ), params)).fetchall():
                doc_to_deal[str(r[0])] = str(r[1]) if r[1] else None
    if not leads_read_all:
        kpids = _ids_of("kp_document")
        if kpids:
            placeholders = ",".join([f":i{i}" for i in range(len(kpids))])
            params = {f"i{i}": v for i, v in enumerate(kpids)}
            for r in (await db.execute(text(
                f"SELECT id, lead_id FROM kp_documents WHERE id IN ({placeholders})"
            ), params)).fetchall():
                kp_to_lead[str(r[0])] = str(r[1]) if r[1] else None
    if not support_read_all:
        sids = _ids_of("support_ticket")
        if sids:
            placeholders = ",".join([f":i{i}" for i in range(len(sids))])
            params = {f"i{i}": v for i, v in enumerate(sids)}
            for r in (await db.execute(text(
                f"SELECT id, created_by_id FROM support_tickets WHERE id IN ({placeholders})"
            ), params)).fetchall():
                sup_to_creator[str(r[0])] = str(r[1]) if r[1] else None

    for row in rows:
        entity_type = row[0]
        entity_id = row[1]
        title = row[2] or ""
        snippet_text = row[3] or ""
        score = float(row[4] or 0)

        # ── Child-entities (task_message / task_subtask) — ВСЕГДА через
        # родительскую задачу, независимо от section_mode. ────────────
        if entity_type in ("task_message", "task_subtask") and not tasks_read_all:
            src_table = "task_messages" if entity_type == "task_message" else "task_subtasks"
            check_sql = f"""
                SELECT 1 FROM {src_table} src
                JOIN tasks t ON t.id = src.task_id
                WHERE src.id = :id AND (
                    t.created_by_user_id = :uid
                    OR t.assigned_to_user_id = :uid
                    OR EXISTS (SELECT 1 FROM task_assignees ta WHERE ta.task_id = t.id AND ta.user_id = :uid)
                    OR EXISTS (SELECT 1 FROM task_watchers tw WHERE tw.task_id = t.id AND tw.user_id = :uid)
                )
            """
            check_res = await db.execute(text(check_sql), {"id": entity_id, "uid": user_id_str})
            if check_res.first() is None:
                continue
            filtered.append(SearchHit(
                entity_type=entity_type, entity_id=entity_id, title=title,
                snippet=snippet_text, score=score,
            ))
            if len(filtered) >= payload.limit:
                break
            continue

        # ── outgoing_document / document — parent = deal. ВСЕГДА (если у
        # юзера нет projects.read_all) проверяем через allowed_deals,
        # эквивалент роутерному гейту на /outgoing-registry и /documents.
        if entity_type == "outgoing_document" and not projects_read_all:
            parent_deal = out_to_deal.get(str(entity_id))
            if parent_deal is None or parent_deal not in (allowed_deals or set()):
                continue
            filtered.append(SearchHit(
                entity_type=entity_type, entity_id=entity_id, title=title,
                snippet=snippet_text, score=score,
            ))
            if len(filtered) >= payload.limit:
                break
            continue
        if entity_type == "document" and not projects_read_all:
            parent_deal = doc_to_deal.get(str(entity_id))
            if parent_deal is None or parent_deal not in (allowed_deals or set()):
                continue
            filtered.append(SearchHit(
                entity_type=entity_type, entity_id=entity_id, title=title,
                snippet=snippet_text, score=score,
            ))
            if len(filtered) >= payload.limit:
                break
            continue

        # ── kp_document — parent = lead. ВСЕГДА (если нет leads.read_all)
        # проверяем через allowed_leads.
        if entity_type == "kp_document" and not leads_read_all:
            parent_lead = kp_to_lead.get(str(entity_id))
            if parent_lead is None or parent_lead not in (allowed_leads or set()):
                continue
            filtered.append(SearchHit(
                entity_type=entity_type, entity_id=entity_id, title=title,
                snippet=snippet_text, score=score,
            ))
            if len(filtered) >= payload.limit:
                break
            continue

        # ── support_ticket — без support.read_all юзер видит только свои
        # тикеты (created_by_id = user.id). Совпадает с роутерной логикой
        # для не-staff юзеров.
        if entity_type == "support_ticket" and not support_read_all:
            creator = sup_to_creator.get(str(entity_id))
            if creator is None or creator != user_id_str:
                continue
            filtered.append(SearchHit(
                entity_type=entity_type, entity_id=entity_id, title=title,
                snippet=snippet_text, score=score,
            ))
            if len(filtered) >= payload.limit:
                break
            continue

        mode = section_modes.get(entity_type)
        if mode == "assigned":
            # Спецкейс для task: пользователь имеет доступ если он creator,
            # main assignee, multi-assignee (task_assignees) или watcher
            # (task_watchers). Это совпадает с логикой роутера /tasks.
            if entity_type == "task":
                check_sql = """
                    SELECT 1 FROM tasks t
                    WHERE t.id = :id AND (
                        t.created_by_user_id = :uid
                        OR t.assigned_to_user_id = :uid
                        OR EXISTS (SELECT 1 FROM task_assignees ta WHERE ta.task_id = t.id AND ta.user_id = :uid)
                        OR EXISTS (SELECT 1 FROM task_watchers tw WHERE tw.task_id = t.id AND tw.user_id = :uid)
                    )
                """
                check_res = await db.execute(text(check_sql), {"id": entity_id, "uid": user_id_str})
                if check_res.first() is None:
                    continue
                # дальше пропускаем общий check_clauses-блок — задача прошла
                filtered.append(SearchHit(
                    entity_type=entity_type, entity_id=entity_id, title=title,
                    snippet=snippet_text, score=score,
                ))
                if len(filtered) >= payload.limit:
                    break
                continue
            # Общий путь: проверяем по owner_col / assigned_col источника.
            acl_info = ENTITY_ACL_MAP[entity_type]
            check_clauses = []
            check_params: Dict[str, Any] = {"id": entity_id, "uid": user_id_str}
            if acl_info["owner_col"]:
                check_clauses.append(f"{acl_info['owner_col']} = :uid")
            if acl_info["assigned_col"]:
                check_clauses.append(f"{acl_info['assigned_col']} = :uid")
            if not check_clauses:
                continue
            check_sql = f"SELECT 1 FROM {acl_info['table']} WHERE id = :id AND ({' OR '.join(check_clauses)})"
            check_res = await db.execute(text(check_sql), check_params)
            if check_res.first() is None:
                continue

        filtered.append(SearchHit(
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            snippet=snippet_text,
            score=score,
        ))
        if len(filtered) >= payload.limit:
            break

    # Обогащаем дочерние сущности parent_id (task_message → task_id,
    # task_subtask → task_id), чтобы фронт открыл правильную карточку.
    child_types = {
        "task_message": ("task_messages", "task_id", "task"),
        "task_subtask": ("task_subtasks", "task_id", "task"),
    }
    child_ids: Dict[str, List[str]] = {}
    for hit in filtered:
        if hit.entity_type in child_types:
            child_ids.setdefault(hit.entity_type, []).append(hit.entity_id)
    for et, ids in child_ids.items():
        table, parent_col, parent_type = child_types[et]
        placeholders_p = ",".join([f":p{i}" for i in range(len(ids))])
        params_p = {f"p{i}": v for i, v in enumerate(ids)}
        rows_p = (await db.execute(text(
            f"SELECT id, {parent_col} FROM {table} WHERE id IN ({placeholders_p})"
        ), params_p)).all()
        parent_map = {str(r[0]): str(r[1]) for r in rows_p if r[1] is not None}
        for hit in filtered:
            if hit.entity_type == et and hit.entity_id in parent_map:
                hit.parent_id = parent_map[hit.entity_id]
                hit.parent_type = parent_type

    return SearchResponse(
        items=filtered,
        total=len(filtered),
        query=payload.query,
        mode="hybrid" if hybrid_active else "fts",
    )
