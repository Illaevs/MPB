"""
Service helper for logging events.
"""
from typing import Optional, Any
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EventLog
from app.services.audit_log import create_audit_log


async def log_event(
    db: AsyncSession,
    entity_type: str,
    action: str,
    entity_id: Optional[str] = None,
    details: Optional[Any] = None,
    created_by: Optional[str] = None,
) -> EventLog:
    if isinstance(details, (dict, list)):
        try:
            details = json.dumps(details, ensure_ascii=True)
        except Exception:
            details = None
    event = await EventLog.create(
        db,
        entity_type=entity_type,
        action=action,
        entity_id=entity_id,
        details=details,
        created_by=created_by,
    )
    try:
        parsed_details = details
        if isinstance(details, str):
            try:
                parsed_details = json.loads(details)
            except Exception:
                parsed_details = details
        await create_audit_log(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=created_by,
            details=parsed_details,
            meta={"source": "event_log"},
            source_event_id=str(event.id),
        )
    except Exception:
        pass
    return event
