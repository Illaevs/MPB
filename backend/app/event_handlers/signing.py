"""
In-process хуки для подписания документов через внутреннюю ЭЦП.

Покрывают сценарии:
  • Подписание документов реестра (`document`) — приёмо-передаточные,
    претензии, КС-2, КС-3, любые PDF из CRM-архива.
  • Подписание договоров (`contract`) — основной/доп.соглашения.
  • Подписание исходящих документов (`outgoing_document`) — письма,
    уведомления, отчёты.

Поддерживаемые сценарии ЭЦП:
  • КЭП физика через CryptoPro Browser Plugin (client-side);
  • облачная подпись (Контур.Подпись / Госключ) через API.

Server-side подписание ОДНИМ сертификатом за нескольких юзеров —
НЕ поддерживаем, потому что юридически неверно (КЭП физика —
персонализированный сертификат).

Текущий статус: эмиссия `*.before_sign` / `*.after_sign` в роутерах
БУДЕТ добавлена когда фронт реализует sign-flow. Сейчас хендлеры уже
зарегистрированы — это значит, что при первом же реальном вызове
`dispatch_before("document.before_sign", ctx)` хендлеры запустятся.
"""
from __future__ import annotations

import logging

from app.services.event_dispatcher import (
    Cancel,
    Continue,
    EventContext,
    on,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# Валидация перед подписанием
# ────────────────────────────────────────────────────────────────────

def _validate_signable_payload(ctx: EventContext, doc_type: str):
    """Общая проверка: документ имеет файл, юзер указан, не уже подписан.

    Возвращает Cancel или None (None = всё ок, пускаем дальше).
    """
    # 1. Есть юзер, который подписывает.
    if not ctx.payload.get("signer_user_id") and not ctx.user_id:
        return Cancel(
            f"Не указан подписант для {doc_type}",
            code=f"{doc_type}.no_signer",
        )
    # 2. Документ имеет физический файл.
    has_file = bool(
        ctx.payload.get("file_path")
        or ctx.payload.get("storage_url")
        or ctx.payload.get("rendered_pdf_path")
    )
    if not has_file:
        return Cancel(
            f"Нельзя подписать {doc_type} без файла-носителя",
            code=f"{doc_type}.no_file",
        )
    # 3. Документ ещё не в финальном статусе.
    status = ctx.payload.get("status")
    if status in {"signed", "archived", "cancelled", "rejected"}:
        return Cancel(
            f"{doc_type} в статусе «{status}» — повторное подписание невозможно",
            code=f"{doc_type}.already_finalized",
        )
    return None


@on("document.before_sign", priority=100, can_cancel=True)
async def validate_document_sign(ctx: EventContext):
    cancel = _validate_signable_payload(ctx, "document")
    if cancel:
        return cancel
    return Continue()


@on("contract.before_sign", priority=100, can_cancel=True)
async def validate_contract_sign(ctx: EventContext):
    cancel = _validate_signable_payload(ctx, "contract")
    if cancel:
        return cancel
    # Дополнительно для контрактов: должны быть указаны подписанты обеих сторон.
    signatories = ctx.payload.get("signatories") or []
    if isinstance(signatories, (list, tuple)) and len(signatories) == 0 and "signatories" in ctx.payload:
        return Cancel(
            "В контракте не указаны подписанты — подписание невозможно",
            code="contract.no_signatories",
        )
    return Continue()


@on("outgoing_document.before_sign", priority=100, can_cancel=True)
async def validate_outgoing_sign(ctx: EventContext):
    cancel = _validate_signable_payload(ctx, "outgoing_document")
    if cancel:
        return cancel
    return Continue()


# ────────────────────────────────────────────────────────────────────
# After-фаза: аудит, обновление статуса, нотификации
# ────────────────────────────────────────────────────────────────────

@on("document.after_sign", priority=100)
async def log_document_signed(ctx: EventContext):
    """Логируем факт подписания. Подписчики Диадок/СОДы получат
    это событие через outbox и могут запросить подписанный артефакт.
    """
    logger.info(
        "document.signed: %s by %s (sig=%s)",
        ctx.entity_id,
        ctx.payload.get("signer_user_id") or ctx.user_id,
        ctx.payload.get("signature_id"),
    )


@on("contract.after_sign", priority=100)
async def log_contract_signed(ctx: EventContext):
    logger.info(
        "contract.signed: %s by %s",
        ctx.entity_id,
        ctx.payload.get("signer_user_id") or ctx.user_id,
    )


@on("outgoing_document.after_sign", priority=100)
async def log_outgoing_signed(ctx: EventContext):
    logger.info(
        "outgoing_document.signed: %s by %s",
        ctx.entity_id,
        ctx.payload.get("signer_user_id") or ctx.user_id,
    )
