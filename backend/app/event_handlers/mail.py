"""
Обработчики для почтовых сообщений (mail_message).

Перед отправкой — валидация получателей/темы.
После приёма — авто-привязка к сущности (deal/contract/...) по
эвристикам в заголовках.
"""
from __future__ import annotations

import logging
import re

from app.services.event_dispatcher import (
    Cancel,
    Continue,
    EventContext,
    on,
)

logger = logging.getLogger(__name__)


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@on("mail_message.before_send", priority=100, can_cancel=True)
async def validate_recipients(ctx: EventContext):
    """Базовая sanity-проверка отправки письма: получатели + тема.

    Глубокую валидацию (антиспам, бан-листы) делаем после интеграции
    с почтовым сервисом — отдельным хендлером с другим priority.
    """
    to = ctx.payload.get("to") or []
    if isinstance(to, str):
        to = [to]
    if not to:
        return Cancel("Не указаны получатели", code="mail.no_recipients")
    bad = [addr for addr in to if not _EMAIL_RE.match(str(addr))]
    if bad:
        return Cancel(
            f"Некорректные email: {', '.join(bad[:3])}",
            code="mail.invalid_email",
        )
    if not (ctx.payload.get("subject") or "").strip():
        return Cancel("Не указана тема письма", code="mail.no_subject")
    return Continue()
