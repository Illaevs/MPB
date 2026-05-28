"""
Notification preferences endpoints for current user.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import NotificationPreference, User
from app.schemas.notification_rules import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

router = APIRouter()


async def _get_or_create_pref(db: AsyncSession, user_id: str) -> NotificationPreference:
    result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == str(user_id)))
    pref = result.scalar_one_or_none()
    if pref:
        return pref
    pref = NotificationPreference(user_id=str(user_id))
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


@router.get("/me", response_model=NotificationPreferenceResponse)
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    return await _get_or_create_pref(db, str(user.id))


@router.put("/me", response_model=NotificationPreferenceResponse)
async def update_my_preferences(
    payload: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    pref = await _get_or_create_pref(db, str(user.id))
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(pref, key, value)
    await db.commit()
    await db.refresh(pref)
    return pref
