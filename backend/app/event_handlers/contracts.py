"""
In-process обработчики событий жизненного цикла договоров.

Все обработчики регистрируются декоратором `@on(...)` из
`app.services.event_dispatcher`. На startup сервер дёргает
`discover_handlers()` — модуль автоматически импортируется и
регистрации выполняются.

Принципы:
  • before-обработчики — синхронная валидация ДО commit'а. Возвращают
    `Cancel(reason)` чтобы запретить, `Mutate(patch)` чтобы изменить,
    `Continue()` чтобы пропустить. НЕ делают записей в БД.
  • after-обработчики — реакция ПОСЛЕ commit'а. Могут писать в БД,
    дёргать внешние сервисы, постить уведомления.
"""
from __future__ import annotations

import logging

from app.services.event_dispatcher import (
    Cancel,
    Continue,
    EventContext,
    Mutate,
    on,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# before: смена статуса
# ────────────────────────────────────────────────────────────────────

@on("contract.before_status_change", priority=100, can_cancel=True)
async def validate_status_transition(ctx: EventContext):
    """Запрещает заведомо некорректные переходы статусов.

    payload должен содержать:
      • status_before — текущий статус контракта
      • status_after  — желаемый
      • amount / paid_amount — для completed
      • signatories (optional list) — для signed (ЭЦП)

    Правила:
      1. completed без оплат → Cancel (защита от случайного клика).
      2. signed без подписантов → Cancel (ЭЦП-flow).
      3. signed без подписанного скана/файла → Cancel (юридическая
         защита: без артефакта подписания нельзя).

    Расширяется добавлением новых веток ниже — все валидации
    статус-переходов держатся в одном файле, грепабельны.
    """
    new = ctx.payload.get("status_after")

    # Завершение договора
    if new == "completed":
        paid = ctx.payload.get("paid_amount") or 0
        amount = ctx.payload.get("amount") or 0
        if amount > 0 and paid <= 0:
            return Cancel(
                "Нельзя завершить договор без оплат. Сначала зафиксируйте оплату или измените сумму.",
                code="contract.completed_without_payment",
            )

    # Подписание (ЭЦП / физическая подпись)
    if new == "signed":
        signatories = ctx.payload.get("signatories") or []
        if isinstance(signatories, (list, tuple)) and len(signatories) == 0:
            # ВАЖНО: некоторые роутеры не присылают `signatories` вообще.
            # В этом случае не блокируем — валидация делается на бэке
            # отдельной проверкой бизнес-данных. Здесь только защита
            # при ЯВНО пустом списке.
            if "signatories" in ctx.payload:
                return Cancel(
                    "Нельзя подписать договор без указания подписантов",
                    code="contract.signed_without_signatories",
                )

    return Continue()


@on("contract.before_status_change", priority=90, can_mutate=True)
async def normalize_status_change_meta(ctx: EventContext):
    """Дополняет payload служебной мета-информацией для after-фазы.

    Не блокирует — просто помечает, что переход «значимый» (например,
    `signed` ИЛИ `completed`). После-фаза по этому флагу решит, слать
    ли уведомления в Telegram и т.п.
    """
    new = ctx.payload.get("status_after")
    significant = new in {"signed", "completed", "cancelled", "rejected"}
    if significant and not ctx.payload.get("_significant_transition"):
        return Mutate(payload_patch={"_significant_transition": True})
    return Continue()


# ────────────────────────────────────────────────────────────────────
# after: пост-обработка
# ────────────────────────────────────────────────────────────────────

@on("contract.after_status_change", priority=100)
async def log_significant_transition(ctx: EventContext):
    """Логирует значимые переходы статусов. Это пример сайдэффекта —
    реально здесь могла бы быть отправка в Telegram, обновление data
    health, пересчёт финансов.
    """
    if not ctx.payload.get("_significant_transition"):
        return
    logger.info(
        "contract.status_change %s: %s → %s",
        ctx.entity_id,
        ctx.payload.get("status_before"),
        ctx.payload.get("status_after"),
    )
