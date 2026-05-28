"""
Inbound приёмник: Telegram Bot API → CRM.

Сценарии:
  • Входящее сообщение от пользователя боту → создание lead или task_message
    (логика маршрутизации зависит от того, привязан ли chat_id к user).
  • Callback от inline-кнопок (approve/reject задачи прямо из чата).

Шаблон по тем же 4 шагам что и `diadoc_inbound.py`:
  1. Верификация подписи (Telegram использует secret_token в заголовке).
  2. Идемпотентность по update_id Telegram.
  3. CRM-side мутация (создание lead/задачи/сообщения).
  4. Эмиссия `*.after_inbound` для downstream-слушателей.

NB: это шаблон для команды интеграции — реальная маршрутизация будет
дописываться при подключении бота.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.event_outbox import emit_event_safe

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_secret() -> str:
    secret = getattr(settings, "TELEGRAM_HMAC_SECRET", None) or ""
    if not secret:
        raise HTTPException(status_code=503, detail="TELEGRAM_HMAC_SECRET не сконфигурирован")
    return secret


def _verify_signature(raw_body: bytes, header_token: Optional[str]) -> bool:
    """Telegram Bot API: сравнение `X-Telegram-Bot-Api-Secret-Token`.
    Это не HMAC, а просто shared-secret; constant-time compare всё равно
    рекомендуется."""
    if not header_token:
        return False
    return hmac.compare_digest(_get_secret(), header_token.strip())


@router.post("/inbound")
async def telegram_inbound(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook-приёмник Telegram Bot API."""
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_telegram_bot_api_secret_token):
        logger.warning("telegram_inbound: bad secret token")
        raise HTTPException(status_code=401, detail="invalid secret token")

    try:
        update: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        logger.warning("telegram_inbound: bad payload: %s", exc)
        raise HTTPException(status_code=400, detail="invalid payload")

    update_id = update.get("update_id")
    if not update_id:
        raise HTTPException(status_code=400, detail="update_id required")

    # Идемпотентность: Telegram переотправляет updates при отсутствии 2xx.
    # Дедуп — отдельная таблица или Redis-кэш (TBD при подключении бота).
    # Здесь shortcut: эмитим событие, дедуп — на стороне consumer'а.

    # Извлекаем основные поля для downstream'а — что внутри payload, зависит
    # от типа update (message/callback_query/edited_message/...).
    message = update.get("message") or update.get("edited_message")
    callback_query = update.get("callback_query")
    kind = "message" if message else ("callback" if callback_query else "other")

    summary_payload = {
        "update_id": update_id,
        "kind": kind,
        "chat_id": (message or {}).get("chat", {}).get("id") if message else None,
        "from_user_id": (message or callback_query or {}).get("from", {}).get("id"),
        "text": (message or {}).get("text") if message else None,
        "callback_data": (callback_query or {}).get("data") if callback_query else None,
        "raw": update,  # полный update передаём подписчикам
    }

    # Эмитим в outbox — реальный маршрутизатор (создание lead'а/task_message'а)
    # будет либо подписчиком этого события, либо отдельным сервисом.
    await emit_event_safe(
        db,
        event_type="telegram_message.after_inbound",
        entity_type="telegram_message",
        entity_id=str(update_id),
        payload=summary_payload,
        payload_version=1,
    )
    await db.commit()

    logger.info("telegram_inbound: ok, update_id=%s kind=%s", update_id, kind)
    return {"ok": True, "update_id": update_id}
