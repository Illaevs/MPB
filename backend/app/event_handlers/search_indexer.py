"""
Step 0 поиска: wildcard-consumer Event Bus → FTS5 indexer.

Это **первый реальный consumer V2** Event Bus.  Архитектурно:
  • Подписан на ВСЕ события через `register_after_emit_hook` (а не через
    `@on(...)`), потому что 99% эмиссий в роутерах идут через
    `emit_event_safe`, который НЕ проходит через `dispatch_after`.
  • При каждом event'е смотрит на `event_type`:
      - `<entity>.after_create / after_update / after_status_change / ...`
        → `index_entity(entity_type, entity_id)`
      - `<entity>.after_delete` → `delete_from_index(entity_type, entity_id)`
  • Идемпотентность: индексация делает свою проверку по content_hash,
    повторные события не приводят к дублям.
  • Soft-fail: исключения внутри индексера логируются, но не валят emit.

Что НЕ индексируется (whitelist в search_indexer.EXTRACTORS):
  • Технические сущности (audit_log, event_*, notification_*, sequences).
  • Сущности с пустым title (экстрактор вернёт None → пропускаем).

Регистрация хука выполняется при загрузке этого модуля (см. вызов
`register_after_emit_hook` в конце файла). Сам модуль импортируется
через `discover_handlers()` в startup (см. `main.py`).
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_outbox import register_after_emit_hook
from app.services.search_indexer import (
    EXTRACTORS,
    delete_from_index_safe,
    index_entity_safe,
)

logger = logging.getLogger(__name__)


# Действия, которые ТРЕБУЮТ переиндексации (любое изменение payload).
# Любое другое — например `.after_send`, `.after_publish` — обычно не
# трогает текстовые поля, но на всякий случай тоже триггерим reindex
# (idempotency защитит от лишней работы).
_REINDEX_ACTIONS = {
    "after_create", "after_update", "after_status_change",
    "after_sign", "after_publish", "after_close",
    "after_render", "after_send", "after_convert_to_deal",
    "after_inbound", "after_role_change", "after_check",
}

_DELETE_ACTIONS = {"after_delete"}


async def _search_indexer_hook(db: AsyncSession, outbox_row) -> None:
    """Универсальный hook, вызываемый из `emit_event` после flush'а.

    Решает по `event_type`, что делать:
      • DELETE — стереть из индекса;
      • Любое другое после-событие — переиндексировать.
      • Игнорируем `*.before_*` и `*.batch_*` (батч-импорт делает
        per-item reindex через свои отдельные create-события).
    """
    event_type = outbox_row.event_type or ""
    entity_type = outbox_row.entity_type or ""
    entity_id = outbox_row.entity_id or ""

    # Игнорируем before-фазу (DRY-RUN на before-стадии не должен
    # триггерить индексацию — payload ещё не сохранён).
    if ".before_" in event_type:
        return
    # batch-события — у них нет entity_id отдельной сущности; пропускаем.
    if ".batch_" in event_type:
        return
    if not entity_type or not entity_id:
        return
    # Если тип не настроен в экстракторах — не тратим время.
    if entity_type not in EXTRACTORS:
        return

    # Разбираем action из event_type (`entity.action_name`).
    try:
        _, action = event_type.split(".", 1)
    except ValueError:
        return

    if action in _DELETE_ACTIONS:
        await delete_from_index_safe(db, entity_type, entity_id)
        logger.debug("indexer: %s/%s removed (event=%s)", entity_type, entity_id, event_type)
        return

    if action in _REINDEX_ACTIONS:
        result = await index_entity_safe(db, entity_type, entity_id)
        logger.debug(
            "indexer: %s/%s -> %s (event=%s)",
            entity_type, entity_id, result, event_type,
        )
        return

    # Неизвестное действие (например, добавили в `_REINDEX_ACTIONS` не
    # все варианты) — на всякий случай тоже переиндексируем. Idempotency
    # защитит от лишней работы (content_hash совпадёт → no-op).
    await index_entity_safe(db, entity_type, entity_id)


# Регистрация хука. Выполняется при первом импорте модуля.
register_after_emit_hook(_search_indexer_hook)
logger.info("search_indexer: registered after_emit hook")
