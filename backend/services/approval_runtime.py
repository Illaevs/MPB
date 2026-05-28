"""
Runtime helpers for approval-aware business actions.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalInstance


async def list_entity_approvals(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> List[ApprovalInstance]:
    result = await db.execute(
        select(ApprovalInstance)
        .where(
            ApprovalInstance.entity_type == str(entity_type),
            ApprovalInstance.entity_id == str(entity_id),
        )
        .order_by(ApprovalInstance.started_at.desc(), ApprovalInstance.created_at.desc())
    )
    return list(result.scalars().all())


async def get_latest_entity_approval(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Optional[ApprovalInstance]:
    items = await list_entity_approvals(db, entity_type, entity_id)
    return items[0] if items else None


async def get_active_entity_approvals(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> List[ApprovalInstance]:
    items = await list_entity_approvals(db, entity_type, entity_id)
    return [item for item in items if item.status == "pending"]


async def ensure_entity_action_allowed(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    action_label: str,
) -> Optional[ApprovalInstance]:
    active_instances = await get_active_entity_approvals(db, entity_type, entity_id)
    if active_instances:
        instance = active_instances[0]
        raise HTTPException(
            status_code=409,
            detail=f"Нельзя выполнить действие «{action_label}»: согласование «{instance.template_name}» еще не завершено.",
        )

    latest_instance = await get_latest_entity_approval(db, entity_type, entity_id)
    if latest_instance and latest_instance.status == "rejected":
        raise HTTPException(
            status_code=409,
            detail=f"Нельзя выполнить действие «{action_label}»: последнее согласование «{latest_instance.template_name}» было отклонено. Запустите согласование заново.",
        )

    return latest_instance
