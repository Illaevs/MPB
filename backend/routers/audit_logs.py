"""
Audit log API (admin only).
"""
import json
from datetime import datetime
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import AuditLog, User

router = APIRouter()


def _is_admin(request: Request) -> bool:
    return bool(getattr(request.state, "is_superuser", False))


def _require_admin(request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")


def _parse_details(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"details": data}
    except Exception:
        return {"details": value}


def _serialize(item: AuditLog) -> Dict[str, Any]:
    return {
        "id": str(item.id),
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "action": item.action,
        "user_id": item.user_id,
        "source_event_id": item.source_event_id,
        "details": _parse_details(item.details),
        "created_at": item.created_at,
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_audit_logs(
    request: Request,
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    limit = min(limit, 200)
    query = select(AuditLog)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == str(entity_id))
    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == str(user_id))
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return [_serialize(item) for item in items]


@router.get("/{entity_type}/{entity_id}", response_model=List[Dict[str, Any]])
async def list_entity_audit_logs(
    entity_type: str,
    entity_id: str,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    limit = min(limit, 200)
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == str(entity_id))
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return [_serialize(item) for item in items]
