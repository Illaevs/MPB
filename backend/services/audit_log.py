"""
Audit log helpers.
"""
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.inspection import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def serialize_model(model: Any) -> Dict[str, Any]:
    if model is None:
        return {}
    mapper = inspect(model)
    data: Dict[str, Any] = {}
    for column in mapper.mapper.column_attrs:
        key = column.key
        try:
            value = getattr(model, key)
        except Exception:
            continue
        data[key] = _normalize_value(value)
    return data


def build_diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    diff: Dict[str, Dict[str, Any]] = {}
    keys = set(before.keys()) | set(after.keys())
    for key in keys:
        before_value = before.get(key)
        after_value = after.get(key)
        if before_value != after_value:
            diff[key] = {"before": before_value, "after": after_value}
    return diff


async def create_audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: Optional[str],
    action: str,
    user_id: Optional[str] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    details: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
    source_event_id: Optional[str] = None,
) -> AuditLog:
    payload: Dict[str, Any] = {}
    if before is not None:
        payload["before"] = before
    if after is not None:
        payload["after"] = after
    if before is not None and after is not None:
        payload["diff"] = build_diff(before, after)
    if details is not None:
        payload["details"] = details
    if meta:
        payload["meta"] = meta

    details_json = json.dumps(payload, ensure_ascii=True) if payload else None
    entry = await AuditLog.create(
        db,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        action=action,
        user_id=str(user_id) if user_id else None,
        source_event_id=source_event_id,
        details=details_json,
    )
    return entry
