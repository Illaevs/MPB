"""
Notifications API Router.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Notification, User
from app.schemas.notification import NotificationResponse

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    unread: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    items = await Notification.list_by_user(
        db,
        str(user.id),
        unread=unread,
        skip=skip,
        limit=limit,
        type_filter=type,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        search=search,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return [NotificationResponse.model_validate(item) for item in items]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await Notification.mark_read(db, notification_id, str(user.id))
    return {"message": "ok"}


@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await Notification.mark_all_read(db, str(user.id))
    return {"message": "ok"}


@router.get("/unread-count")
async def unread_notifications_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == str(user.id),
            Notification.is_read.is_(False),
            (Notification.deliver_at.is_(None)) | (Notification.deliver_at <= func.now()),
        )
    )
    return {"count": int(result.scalar() or 0)}
