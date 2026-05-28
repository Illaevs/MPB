"""
PILOT inbound-приёмник: Контур.Диадок → CRM.

Сценарии:
  • Диадок присылает статус-апдейт по нашему исходящему документу
    (acceptDocument / rejectDocument / sign / archive);
  • Диадок присылает входящий документ от контрагента (новый/доп.договор,
    счёт, ТОРГ-12, акт КС-2 от подрядчика).

Что делает приёмник (ровно эти 4 шага в одной транзакции):
  1. Проверяет HMAC-подпись Header `X-Diadoc-Signature` через shared secret;
  2. Дедуп по external_id (Диадоковский messageId) — повтор возвращает 200 OK;
  3. Создаёт CRM-документ (`Document` в реестре документов);
  4. Эмитит `document.after_inbound` для внутренних слушателей через outbox.

NB: boevoye подключение к Диадоку пойдёт после E-фазы — сейчас это
шаблон без реального HTTP-клиента, чтобы по нему могли строиться
остальные интеграции (Госключ / Банк / 1С / СОДы).  Целевые форматы
payload определит инженер по интеграции — см. docs/integrations/diadoc.md (TBD).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.models import Document
from app.services.event_outbox import emit_event_safe

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────────────────────────────────────────────────
# Step 1. Проверка HMAC-подписи.
# Secret лежит в ENV (`DIADOC_HMAC_SECRET`).  Fail-closed: пустой
# secret → 503 Service Unavailable (значит, интеграция не настроена).
# ────────────────────────────────────────────────────────────────────

def _get_hmac_secret() -> str:
    secret = getattr(settings, "DIADOC_HMAC_SECRET", None) or ""
    if not secret:
        # Не отдаём 401 — клиент не должен думать, что подпись неверна;
        # это про конфигурацию на нашей стороне.
        raise HTTPException(
            status_code=503,
            detail="DIADOC_HMAC_SECRET не сконфигурирован",
        )
    return secret


def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """`X-Diadoc-Signature` — hex-digest HMAC-SHA256(body, secret)."""
    if not signature_header:
        return False
    expected = hmac.new(
        _get_hmac_secret().encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    # constant-time comparison — защита от timing-side-channel
    return hmac.compare_digest(expected, signature_header.strip())


# ────────────────────────────────────────────────────────────────────
# Step 2. Pydantic-схема payload.
# Минимальная для пилота: в реале Диадок шлёт большую структуру с
# XML-эталонами и приложениями, мы вытаскиваем только то, что нужно
# для отражения документа в реестре CRM.
# ────────────────────────────────────────────────────────────────────

class DiadocInboundPayload(BaseModel):
    message_id: str = Field(description="Диадоковский external_id — для дедупа и трассировки")
    document_type: str = Field(description="contract | act | ks-2 | invoice | torg-12 | ...")
    title: str
    counterparty_inn: str = Field(description="ИНН отправителя — для матчинга на наших companies")
    document_date: Optional[str] = Field(None, description="ISO дата документа (если есть)")
    pdf_url: Optional[str] = Field(None, description="URL подписанного PDF — скачаем отдельным заданием")
    event_kind: str = Field(
        default="received",
        description="received | signed | rejected | archived — что сделал Диадок",
    )


# ────────────────────────────────────────────────────────────────────
# Эндпоинт.  ВАЖНО: маршрут НЕ висит под обычной cookie-аутентификацией
# (см. main.py → AuthMiddleware → open_prefixes).  Аутентификация
# обеспечивается HMAC-подписью + IP allow-list на уровне nginx.
# ────────────────────────────────────────────────────────────────────

@router.post("/inbound")
async def diadoc_inbound(
    request: Request,
    x_diadoc_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Приёмник вебхуков Диадока.

    NB: FastAPI обычно сам парсит JSON, но для HMAC нам нужен СЫРОЙ body,
    поэтому читаем bytes сами, потом валидируем Pydantic-схемой.
    """
    raw_body = await request.body()

    # Step 1: верификация подписи (fail-closed).
    if not _verify_signature(raw_body, x_diadoc_signature):
        logger.warning(
            "diadoc_inbound: bad/missing signature (len=%d, sig=%r)",
            len(raw_body), x_diadoc_signature,
        )
        raise HTTPException(status_code=401, detail="invalid signature")

    # Step 2: парсим payload (после подписи — иначе DoS-ом можно
    # потратить CPU на парсинг без подписи).
    try:
        payload_dict = json.loads(raw_body.decode("utf-8"))
        payload = DiadocInboundPayload(**payload_dict)
    except Exception as exc:
        logger.warning("diadoc_inbound: bad payload: %s", exc)
        raise HTTPException(status_code=400, detail="invalid payload")

    # Step 3a: idempotency check.  Если такой external_id уже регистрировали —
    # возвращаем 200 OK без побочных эффектов (важно для повторов Диадока
    # из-за сетевых сбоев).
    existing = await db.execute(
        select(Document).where(
            Document.source_type == "diadoc",
            Document.source_id == payload.message_id,
        )
    )
    existing_doc = existing.scalar_one_or_none()
    if existing_doc:
        logger.info(
            "diadoc_inbound: deduplicated %s (existing doc=%s)",
            payload.message_id, existing_doc.id,
        )
        return {"status": "ok", "deduplicated": True, "document_id": existing_doc.id}

    # Step 3b: CRM-side мутация — создаём строку в реестре документов.
    doc = Document(
        doc_type=payload.document_type,
        title=payload.title,
        status="received",
        source_type="diadoc",
        source_id=payload.message_id,
    )
    db.add(doc)
    await db.flush()  # получили doc.id для emit ниже

    # Step 4: эмитим event для внутренних слушателей.  Indexer / BI /
    # Telegram-нотификации подхватят через outbox-воркер.  payload_version=1
    # фиксируем сразу, чтобы потом мигрировать схему без боли.
    await emit_event_safe(
        db,
        event_type="document.after_inbound",
        entity_type="document",
        entity_id=str(doc.id),
        payload={
            "source": "diadoc",
            "external_id": payload.message_id,
            "doc_type": payload.document_type,
            "counterparty_inn": payload.counterparty_inn,
            "document_date": payload.document_date,
            "pdf_url": payload.pdf_url,
            "event_kind": payload.event_kind,
        },
        payload_version=1,
    )

    await db.commit()

    logger.info(
        "diadoc_inbound: created document %s from diadoc message %s",
        doc.id, payload.message_id,
    )
    return {"status": "ok", "document_id": doc.id, "deduplicated": False}
