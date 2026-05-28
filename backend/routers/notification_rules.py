"""
Notification rules management endpoints (admin/superuser only).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import NotificationRule, User
from app.schemas.notification_rules import (
    NotificationRuleCreate,
    NotificationRuleResponse,
    NotificationRuleUpdate,
)

router = APIRouter()


def _is_admin(request: Request) -> bool:
    return bool(getattr(request.state, "is_superuser", False))


def _require_admin(request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/", response_model=List[NotificationRuleResponse])
async def list_rules(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    result = await db.execute(select(NotificationRule).order_by(NotificationRule.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=NotificationRuleResponse)
async def create_rule(
    payload: NotificationRuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    rule = await NotificationRule.create(
        db,
        **payload.dict(),
        created_by=str(user.id),
    )
    return rule


@router.put("/{rule_id}", response_model=NotificationRuleResponse)
async def update_rule(
    rule_id: str,
    payload: NotificationRuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    rule = await NotificationRule.update(db, rule_id, **payload.dict(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    _require_admin(request)
    rule = await NotificationRule.get_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "deleted"}
