"""
Inbound приёмник: банковские выписки → CRM.

Сценарии:
  • Загрузка XML/CSV выписки в формате 1С 1.03 (универсальный обмен).
  • Альтернатива — push от банк-клиента (если поддерживает webhook'и).

Шаблон по тем же 4 шагам:
  1. HMAC-подпись (для push) или multipart file upload (для XML).
  2. Идемпотентность по `BIK + ACCOUNT + DATE_FROM/DATE_TO + HASH(content)`.
  3. CRM-мутация: создаём `TreasuryTransaction` строки + связываем к auto_rule.
  4. Эмиссия `treasury_transaction.batch_imported` — она ✅ УЖЕ реализована
     (`emit_batch_event`), просто здесь точка вызова.

Pilot: только endpoint-шаблон. Реальный парсер XML 1С 1.03 — отдельный сервис
`bank_statement_parser.py`, подключится в июле.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.services.event_outbox import emit_batch_event_safe

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_secret() -> str:
    secret = getattr(settings, "BANK_HMAC_SECRET", None) or ""
    if not secret:
        raise HTTPException(status_code=503, detail="BANK_HMAC_SECRET не сконфигурирован")
    return secret


def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not signature_header:
        return False
    expected = hmac.new(_get_secret().encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())


@router.post("/inbound")
async def bank_inbound(
    request: Request,
    file: UploadFile = File(...),
    x_bank_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Принимает XML/CSV выписку в формате 1С 1.03.

    Подпись: HMAC-SHA256 по сырому body файла. Без подписи — отказ.

    После парсинга — эмитит ОДНО batch-событие на всю пачку транзакций
    (см. `emit_batch_event` в services/event_outbox.py — это паттерн для
    1С/банк-консьюмеров, чтобы они получали пачку атомарно).
    """
    if file is None:
        raise HTTPException(status_code=400, detail="file required")

    content = await file.read()

    if not _verify_signature(content, x_bank_signature):
        logger.warning("bank_inbound: bad signature, filename=%s size=%d", file.filename, len(content))
        raise HTTPException(status_code=401, detail="invalid signature")

    # TODO: парсинг XML 1С 1.03 → list of {amount, date, payer, payee, purpose, ...}
    # Сейчас pilot: эмитим событие "выписка получена" с сырым содержимым (hash).
    content_hash = hashlib.sha256(content).hexdigest()

    # Шаблонная эмиссия — `items` будут наполнены реальными транзакциями
    # после реализации парсера.
    await emit_batch_event_safe(
        db,
        event_type="treasury_transaction.batch_imported",
        entity_type="treasury_transaction",
        items=[],  # TODO: заполнить после парсинга
        parent_id=None,
        summary={
            "source": "bank_statement",
            "filename": file.filename,
            "size_bytes": len(content),
            "content_hash": content_hash,
            "parsed_count": 0,  # будет реальное число после парсинга
        },
    )
    await db.commit()

    logger.info("bank_inbound: received %s (%d bytes, hash=%s)", file.filename, len(content), content_hash[:12])
    return {"ok": True, "filename": file.filename, "content_hash": content_hash}
