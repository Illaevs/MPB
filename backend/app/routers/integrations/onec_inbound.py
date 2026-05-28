"""
Inbound приёмник: 1С Бухгалтерия 8.3 → CRM.

Сценарии:
  • 1С присылает изменения контрагентов (обновили реквизиты в БК).
  • 1С присылает новые/обновлённые платежи (выписки уже обработаны в 1С).
  • 1С присылает изменения счетов/договоров.

Шаблон по тем же 4 шагам:
  1. HMAC-подпись (1С использует HTTP-сервис; secret настраивается в конфиге БК).
  2. Идемпотентность по external_id 1С (uuid из БК).
  3. CRM-мутация (создание/обновление SubcontractorCard / TreasuryTransaction
     / IncomeExpenseEntry — в зависимости от entity_type в payload).
  4. Эмиссия `*.after_inbound` событий.

Реальная маршрутизация (какой entity на нашей стороне создавать/обновлять)
делается командой 1С-интеграции в июле.
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
    secret = getattr(settings, "ONEC_HMAC_SECRET", None) or ""
    if not secret:
        raise HTTPException(status_code=503, detail="ONEC_HMAC_SECRET не сконфигурирован")
    return secret


def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not signature_header:
        return False
    expected = hmac.new(_get_secret().encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())


@router.post("/inbound")
async def onec_inbound(
    request: Request,
    x_onec_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Webhook-приёмник 1С.

    Ожидаемый payload (договорённость с командой 1С):
    ```json
    {
      "external_id": "<uuid из 1С>",
      "entity_type": "counterparty|payment|invoice|contract",
      "action": "created|updated|deleted",
      "data": { ... сам объект 1С ... }
    }
    ```
    """
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_onec_signature):
        logger.warning("onec_inbound: bad signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        logger.warning("onec_inbound: bad payload: %s", exc)
        raise HTTPException(status_code=400, detail="invalid payload")

    external_id = payload.get("external_id")
    entity_type = payload.get("entity_type")
    action = payload.get("action")
    data = payload.get("data") or {}

    if not external_id or not entity_type or not action:
        raise HTTPException(status_code=400, detail="external_id, entity_type, action required")

    # Идемпотентность — реализуется при подключении (нужно хранить таблицу
    # обработанных external_id × entity_type).

    # Шаблонное событие — реальные обработчики (создание/обновление сущности
    # на нашей стороне) подключатся через `@on("onec_*.after_inbound")`.
    await emit_event_safe(
        db,
        event_type=f"onec_{entity_type}.after_inbound",
        entity_type=f"onec_{entity_type}",
        entity_id=str(external_id),
        payload={
            "external_id": external_id,
            "entity_type": entity_type,
            "action": action,
            "data": data,
        },
        payload_version=1,
    )
    await db.commit()

    logger.info("onec_inbound: ok, entity=%s/%s action=%s", entity_type, external_id, action)
    return {"ok": True, "external_id": external_id}
