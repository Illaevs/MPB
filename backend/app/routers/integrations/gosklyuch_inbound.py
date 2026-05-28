"""
Inbound приёмник: Госключ ЭЦП → CRM.

Сценарий:
  • Пользователь подписал документ через мобильное приложение Госключ.
  • Госключ присылает callback с signature blob'ом → мы сохраняем подпись
    на стороне CRM, обновляем статус документа на 'signed', эмитим
    `document.after_sign`.

Шаблон по тем же 4 шагам.

Pilot: только endpoint-шаблон. Реальный формат callback'а Госключа
определяется при подключении (требует регистрации API-ключа в Минцифре).
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
    secret = getattr(settings, "GOSKLYUCH_HMAC_SECRET", None) or ""
    if not secret:
        raise HTTPException(status_code=503, detail="GOSKLYUCH_HMAC_SECRET не сконфигурирован")
    return secret


def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not signature_header:
        return False
    expected = hmac.new(_get_secret().encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())


@router.post("/inbound")
async def gosklyuch_inbound(
    request: Request,
    x_gosklyuch_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook Госключа.

    Ожидаемый payload (договорённость с интеграцией):
    ```json
    {
      "request_id": "<id запроса на подпись>",
      "document_id": "<id документа в CRM>",
      "user_id": "<id пользователя в CRM>",
      "status": "signed|rejected|cancelled",
      "signature_blob": "<base64 PKCS#7>",
      "signed_at": "<ISO timestamp>"
    }
    ```
    """
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_gosklyuch_signature):
        logger.warning("gosklyuch_inbound: bad signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        logger.warning("gosklyuch_inbound: bad payload: %s", exc)
        raise HTTPException(status_code=400, detail="invalid payload")

    request_id = payload.get("request_id")
    document_id = payload.get("document_id")
    user_id = payload.get("user_id")
    status = payload.get("status")

    if not (request_id and document_id and status):
        raise HTTPException(status_code=400, detail="request_id, document_id, status required")

    # Шаблон: реальный update Document.status + сохранение signature_blob
    # будет в hooks `@on("gosklyuch.after_inbound")`.

    # Эмитим внутреннее событие, ИДЕЯ:
    # - `gosklyuch.after_inbound` ловит in-process handler, который:
    #   a) сохраняет signature_blob в storage;
    #   b) обновляет Document.status = 'signed';
    #   c) триггерит `document.after_sign` (уже есть в E1).
    await emit_event_safe(
        db,
        event_type="gosklyuch.after_inbound",
        entity_type="gosklyuch_signature",
        entity_id=str(request_id),
        payload={
            "request_id": request_id,
            "document_id": document_id,
            "user_id": user_id,
            "status": status,
            "signed_at": payload.get("signed_at"),
            "has_blob": bool(payload.get("signature_blob")),
        },
        payload_version=1,
    )
    await db.commit()

    logger.info("gosklyuch_inbound: ok request_id=%s status=%s", request_id, status)
    return {"ok": True, "request_id": request_id}
