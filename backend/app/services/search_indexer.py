"""
Step 0 поиска: in-process indexer service.

Что делает:
  • `index_entity(db, entity_type, entity_id)` — извлекает свежий объект,
    собирает title+content через per-entity extractor, делает upsert
    в `search_fts` и обновляет `search_index_meta`.
  • `delete_from_index(db, entity_type, entity_id)` — стирает строку из
    `search_fts` и `search_index_meta`.
  • Идемпотентность: считаем `content_hash`. Если совпал с прошлым —
    skip (важно для wildcard-консьюмера, потому что одна логическая
    операция может прислать несколько `*.after_update` событий).

Извлекатели (extractors): per-entity мапа из `entity_type → callable`,
которая принимает SQLAlchemy-объект и возвращает `{title, content}`.

Поддерживаемые типы на старте (расширяем по запросу):
  • deal, contract, lead, company, task, document, outgoing_document,
    kp_document, mail_message, legal_case, support_ticket,
    task_message, task_subtask, subcontractor_card.

Какие сущности НЕ индексируем (антипаттерны):
  • event_outbox / event_subscription / event_log / event_delivery_dedup
    — техническая инфра шины;
  • audit_log — журнал событий, индексировать его = индексировать
    индексацию (бесконечный цикл);
  • notification_* — внутренние нотификации;
  • любые `_sequence`, `_dedup`, `_link` — служебные.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# Per-entity extractors. Возвращают (title, content) либо None если
# сущность не подлежит индексации.
#
# title: одна короткая строка для показа в результатах и для BM25-boost.
# content: длинный текст со всем что имеет смысл искать (description,
#          адрес, заметки, ИНН, реквизиты, теги — всё, что вспомнится).
# ────────────────────────────────────────────────────────────────────

def _extract_deal(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or "").strip()
    content_parts = [
        getattr(entity, "obj_name", None),
        getattr(entity, "address", None),
        getattr(entity, "object_type", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    if not title:
        return None
    return title, content


def _extract_contract(entity) -> Optional[Tuple[str, str]]:
    num = getattr(entity, "contract_number", None) or ""
    contract_type = getattr(entity, "contract_type", None) or ""
    title = f"Договор № {num}".strip() if num else "Договор"
    content_parts = [str(contract_type)]
    content = "\n".join([p for p in content_parts if p])
    return title, content


def _extract_lead(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or "").strip()
    content_parts = [
        getattr(entity, "description", None),
        getattr(entity, "address", None),
        getattr(entity, "notes", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    if not title:
        return None
    return title, content


def _extract_company(entity) -> Optional[Tuple[str, str]]:
    name = (getattr(entity, "name", None) or "").strip()
    if not name:
        return None
    content_parts = [
        getattr(entity, "short_name", None),
        getattr(entity, "full_name", None),
        getattr(entity, "inn", None),
        getattr(entity, "kpp", None),
        getattr(entity, "ogrn", None),
        getattr(entity, "address", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return name, content


def _extract_task(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or "").strip()
    if not title:
        return None
    return title, (getattr(entity, "description", None) or "")


def _extract_document(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or "").strip()
    if not title:
        return None
    content_parts = [
        getattr(entity, "doc_type", None),
        getattr(entity, "number", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return title, content


def _extract_outgoing_document(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or getattr(entity, "subject", None) or "").strip()
    content_parts = [
        getattr(entity, "body", None),
        getattr(entity, "number", None),
        getattr(entity, "kind", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return title or "Исходящий документ", content


def _extract_kp_document(entity) -> Optional[Tuple[str, str]]:
    num = getattr(entity, "number_display", None) or ""
    title = f"КП № {num}".strip() if num else "Коммерческое предложение"
    return title, ""


def _extract_mail_message(entity) -> Optional[Tuple[str, str]]:
    subject = (getattr(entity, "subject", None) or "").strip()
    if not subject and not getattr(entity, "body_preview", None):
        return None
    content_parts = [
        getattr(entity, "from_address", None),
        getattr(entity, "to_addresses", None),
        getattr(entity, "body_preview", None),
        getattr(entity, "snippet", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return subject or "Письмо", content


def _extract_legal_case(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "case_number", None) or "").strip()
    if not title:
        return None
    content_parts = [
        getattr(entity, "judge", None),
        getattr(entity, "jurisdiction", None),
        getattr(entity, "description", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return f"Дело № {title}", content


def _extract_support_ticket(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "subject", None) or getattr(entity, "title", None) or "").strip()
    if not title:
        return None
    return title, (getattr(entity, "description", None) or "")


def _extract_task_message(entity) -> Optional[Tuple[str, str]]:
    body = (getattr(entity, "body", None) or "").strip()
    if not body or getattr(entity, "is_deleted", False):
        return None
    return body[:80], body


def _extract_task_subtask(entity) -> Optional[Tuple[str, str]]:
    title = (getattr(entity, "title", None) or "").strip()
    if not title:
        return None
    return title, ""


def _extract_subcontractor_card(entity) -> Optional[Tuple[str, str]]:
    name = (getattr(entity, "title", None) or "").strip()
    if not name:
        return None
    content_parts = [
        getattr(entity, "inn", None),
        getattr(entity, "specialization", None),
        getattr(entity, "notes", None),
    ]
    content = "\n".join([str(p) for p in content_parts if p])
    return name, content


# Реестр экстракторов. Ключ — entity_type как в emit_event.
EXTRACTORS: Dict[str, Callable[[Any], Optional[Tuple[str, str]]]] = {
    "deal": _extract_deal,
    "contract": _extract_contract,
    "lead": _extract_lead,
    "company": _extract_company,
    "task": _extract_task,
    "document": _extract_document,
    "outgoing_document": _extract_outgoing_document,
    "kp_document": _extract_kp_document,
    "mail_message": _extract_mail_message,
    "legal_case": _extract_legal_case,
    "support_ticket": _extract_support_ticket,
    "task_message": _extract_task_message,
    "task_subtask": _extract_task_subtask,
    "subcontractor_card": _extract_subcontractor_card,
}


# Маппинг entity_type → SQLAlchemy class. Лениво импортируем чтобы
# не было циклов.
def _get_entity_class(entity_type: str):
    from app.models import (
        Deal, Contract, Lead, Company, Task,
        Document, OutgoingDocument, MailMessage,
        LegalCase, SupportTicket, TaskMessage, TaskSubtask,
        SubcontractorCard,
    )
    from app.models.kp import KpDocument
    return {
        "deal": Deal,
        "contract": Contract,
        "lead": Lead,
        "company": Company,
        "task": Task,
        "document": Document,
        "outgoing_document": OutgoingDocument,
        "kp_document": KpDocument,
        "mail_message": MailMessage,
        "legal_case": LegalCase,
        "support_ticket": SupportTicket,
        "task_message": TaskMessage,
        "task_subtask": TaskSubtask,
        "subcontractor_card": SubcontractorCard,
    }.get(entity_type)


def _hash_content(title: str, content: str) -> str:
    """Стабильный хэш для проверки «изменилось ли что-то с прошлой
    индексации». SHA-256 hex (64 char) — впишется в VARCHAR(64) meta."""
    h = hashlib.sha256()
    h.update((title or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((content or "").encode("utf-8"))
    return h.hexdigest()


# ────────────────────────────────────────────────────────────────────
# Public API.
# ────────────────────────────────────────────────────────────────────

async def index_entity(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Optional[str]:
    """Проиндексировать одну сущность.

    Возвращает:
      • "indexed"    — добавили/обновили строку в FTS;
      • "skipped"    — content_hash совпал, ничего не делали;
      • "no_extractor" — для этого entity_type индексация не настроена;
      • "not_found"  — объекта нет в БД (был удалён?);
      • None         — ошибка (см. логи).
    """
    if entity_type not in EXTRACTORS:
        return "no_extractor"
    entity_class = _get_entity_class(entity_type)
    if entity_class is None:
        return "no_extractor"

    # Некоторые модели (Contract, OutgoingDocument) используют UUID(as_uuid=True)
    # как PK. Если entity_id передан строкой — пробуем сконвертировать,
    # иначе db.get падает на process step. Если конверсия не удаётся —
    # значит ключ строковый, передаём как есть.
    pk_value: Any = entity_id
    try:
        import uuid as _uuid
        pk_value = _uuid.UUID(str(entity_id))
    except (ValueError, AttributeError, TypeError):
        pk_value = entity_id

    try:
        entity = await db.get(entity_class, pk_value)
    except Exception:
        # Если UUID-конверсия привела к ошибке (например, ключ STRING а
        # модель ожидает что-то другое) — fallback на исходный entity_id.
        entity = await db.get(entity_class, entity_id)
    if entity is None:
        # Может быть гонка: событие after_create ещё не доехало до commit'а
        # либо запись удалили до того как мы её прочитали. Логируем и идём.
        logger.debug("index_entity: %s/%s not found in DB", entity_type, entity_id)
        return "not_found"

    extracted = EXTRACTORS[entity_type](entity)
    if extracted is None:
        # Экстрактор отказался — например, пустой title. Удалим из индекса
        # на всякий случай (вдруг там был старый snapshot).
        await delete_from_index(db, entity_type, entity_id)
        return "no_content"

    title, content = extracted
    content_hash = _hash_content(title, content)

    # Идемпотентность: если hash совпал — пропускаем upsert (важно для
    # wildcard-консьюмера, потому что одна логическая операция может
    # прислать несколько `*.after_update` событий).
    existing = await db.execute(
        text("SELECT content_hash FROM search_index_meta WHERE entity_type = :et AND entity_id = :eid"),
        {"et": entity_type, "eid": str(entity_id)},
    )
    row = existing.first()
    if row and row[0] == content_hash:
        return "skipped"

    # Удаляем старую строку из FTS (FTS5 без UPSERT — только DELETE+INSERT).
    await db.execute(
        text("DELETE FROM search_fts WHERE entity_type = :et AND entity_id = :eid"),
        {"et": entity_type, "eid": str(entity_id)},
    )
    # Вставляем свежую.
    await db.execute(
        text("""
            INSERT INTO search_fts (entity_type, entity_id, title, content)
            VALUES (:et, :eid, :title, :content)
        """),
        {"et": entity_type, "eid": str(entity_id), "title": title, "content": content},
    )
    # Обновляем meta.
    if row:
        await db.execute(
            text("""
                UPDATE search_index_meta
                SET content_hash = :hash, last_indexed_at = CURRENT_TIMESTAMP
                WHERE entity_type = :et AND entity_id = :eid
            """),
            {"hash": content_hash, "et": entity_type, "eid": str(entity_id)},
        )
    else:
        await db.execute(
            text("""
                INSERT INTO search_index_meta (entity_type, entity_id, content_hash)
                VALUES (:et, :eid, :hash)
            """),
            {"et": entity_type, "eid": str(entity_id), "hash": content_hash},
        )

    logger.debug("index_entity: %s/%s indexed (title=%r)", entity_type, entity_id, title[:60])
    return "indexed"


async def delete_from_index(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> None:
    """Стереть сущность из индекса. Idempotent — не падает если её там нет."""
    await db.execute(
        text("DELETE FROM search_fts WHERE entity_type = :et AND entity_id = :eid"),
        {"et": entity_type, "eid": str(entity_id)},
    )
    await db.execute(
        text("DELETE FROM search_index_meta WHERE entity_type = :et AND entity_id = :eid"),
        {"et": entity_type, "eid": str(entity_id)},
    )
    logger.debug("delete_from_index: %s/%s removed", entity_type, entity_id)


async def index_entity_safe(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Optional[str]:
    """Обёртка, которая глотает любые исключения и логирует. Использовать
    в event-bus handlers — индексация не должна валить бизнес-операцию."""
    try:
        return await index_entity(db, entity_type, entity_id)
    except Exception as exc:
        logger.warning("index_entity_safe swallowed error: %s", exc, exc_info=True)
        return None


async def delete_from_index_safe(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> None:
    try:
        await delete_from_index(db, entity_type, entity_id)
    except Exception as exc:
        logger.warning("delete_from_index_safe swallowed error: %s", exc, exc_info=True)
