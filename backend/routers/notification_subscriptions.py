"""
Notification subscriptions endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import NotificationSubscription, User
from app.schemas.notification_rules import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
    NotificationSubscriptionUpdate,
)

router = APIRouter()


@router.get("/me", response_model=List[NotificationSubscriptionResponse])
async def list_subscriptions(
    entity_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    query = select(NotificationSubscription).where(NotificationSubscription.user_id == str(user.id))
    if entity_type:
        query = query.where(NotificationSubscription.entity_type == entity_type)
    result = await db.execute(query.order_by(NotificationSubscription.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=NotificationSubscriptionResponse)
async def create_subscription(
    payload: NotificationSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.user_id == str(user.id),
            NotificationSubscription.entity_type == payload.entity_type,
            NotificationSubscription.entity_id == payload.entity_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    sub = NotificationSubscription(
        user_id=str(user.id),
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.patch("/{subscription_id}", response_model=NotificationSubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    payload: NotificationSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.id == subscription_id,
            NotificationSubscription.user_id == str(user.id),
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(sub, key, value)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/")
async def delete_subscription(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await db.execute(
        delete(NotificationSubscription).where(
            NotificationSubscription.user_id == str(user.id),
            NotificationSubscription.entity_type == entity_type,
            NotificationSubscription.entity_id == entity_id,
        )
    )
    await db.commit()
    return {"message": "deleted"}
