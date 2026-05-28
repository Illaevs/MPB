"""Absences API — отпуска / больничные / командировки сотрудников.

Эндпоинты:
- GET    /absences                  — список с фильтрами
- POST   /absences                  — создать (свой или, для админа, чужой)
- PATCH  /absences/{id}             — править
- DELETE /absences/{id}             — удалить

Видимость:
- `absences.read_all` (или users.edit_all/superuser) — видит все записи
- иначе пользователь видит только свои

Правка:
- свои записи — нужен `absences.edit_assigned` (или edit_all)
- чужие — только `absences.edit_all` или admin
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import User, UserAbsence
from app.schemas.profile import (
    AbsenceCreate,
    AbsencePatch,
    AbsenceResponse,
    ABSENCE_TYPES,
)
from app.services.permissions import get_section_acl, is_superuser


router = APIRouter()


# ---- helpers -------------------------------------------------------------

async def _is_admin(db: AsyncSession, request: Request, me: User) -> bool:
    """Админ для целей правки чужих отсутствий: `absences.edit_all`
    или `users.edit_all` (HR-роль), или superuser."""
    if is_superuser(request):
        return True
    acl = await get_section_acl(db, me.role_id, "absences")
    if acl.edit_all:
        return True
    acl_u = await get_section_acl(db, me.role_id, "users")
    return bool(acl_u.edit_all)


async def _can_read_others(db: AsyncSession, request: Request, me: User) -> bool:
    if is_superuser(request):
        return True
    acl = await get_section_acl(db, me.role_id, "absences")
    if acl.read_all or acl.edit_all:
        return True
    acl_u = await get_section_acl(db, me.role_id, "users")
    return bool(acl_u.read_all or acl_u.edit_all)


async def _to_resp(db: AsyncSession, a: UserAbsence) -> AbsenceResponse:
    name = None
    creator_name = None
    if a.user_id:
        row = (await db.execute(
            select(User.full_name).where(User.id == str(a.user_id))
        )).scalar_one_or_none()
        name = row
    if a.created_by:
        row = (await db.execute(
            select(User.full_name).where(User.id == str(a.created_by))
        )).scalar_one_or_none()
        creator_name = row
    return AbsenceResponse(
        id=str(a.id),
        user_id=str(a.user_id),
        type=a.type,
        date_from=a.date_from,
        date_to=a.date_to,
        comment=a.comment,
        created_by=str(a.created_by) if a.created_by else None,
        created_at=a.created_at,
        updated_at=a.updated_at,
        user_full_name=name,
        created_by_full_name=creator_name,
    )


def _check_dates(date_from: date, date_to: date):
    if date_from > date_to:
        raise HTTPException(
            status_code=400, detail="Дата окончания должна быть не раньше начала",
        )


# ---- endpoints -----------------------------------------------------------

@router.get("", response_model=List[AbsenceResponse])
async def list_absences(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    user_id: Optional[str] = Query(None),
    type_: Optional[str] = Query(None, alias="type"),
    from_: Optional[date] = Query(None, alias="from"),
    to: Optional[date] = Query(None),
):
    """Список отсутствий с фильтрами.

    Пересечение по периоду: запись попадает, если её интервал
    [date_from, date_to] пересекается с [from, to] (если фильтр задан)."""
    sees_others = await _can_read_others(db, request, user)
    conds = []
    if not sees_others:
        conds.append(UserAbsence.user_id == str(user.id))
    elif user_id:
        conds.append(UserAbsence.user_id == str(user_id))
    if type_:
        if type_ not in ABSENCE_TYPES:
            raise HTTPException(status_code=400, detail="Неизвестный тип")
        conds.append(UserAbsence.type == type_)
    if from_:
        conds.append(UserAbsence.date_to >= from_)
    if to:
        conds.append(UserAbsence.date_from <= to)

    q = select(UserAbsence)
    if conds:
        q = q.where(and_(*conds))
    q = q.order_by(UserAbsence.date_from.desc())
    res = await db.execute(q)
    rows = res.scalars().all()
    return [await _to_resp(db, a) for a in rows]


@router.post("", response_model=AbsenceResponse)
async def create_absence(
    payload: AbsenceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать запись об отсутствии.

    - Если `user_id` не указан — создаётся «свою».
    - Если указан чужой `user_id` — нужно админство.
    - Любой может создавать свою (раздел `absences.edit_assigned`)."""
    target_id = payload.user_id or str(user.id)
    if target_id != str(user.id):
        if not await _is_admin(db, request, user):
            raise HTTPException(
                status_code=403, detail="Можно создавать только свои отсутствия",
            )
        exists = (await db.execute(
            select(User.id).where(User.id == str(target_id))
        )).scalar_one_or_none()
        if not exists:
            raise HTTPException(status_code=400, detail="Сотрудник не найден")
    else:
        # «Своё» — проверим, что секция включена для роли (edit_assigned/all).
        # Без секции совсем — 403.
        acl = await get_section_acl(db, user.role_id, "absences")
        if not (acl.edit_all or acl.edit_assigned):
            if not is_superuser(request):
                raise HTTPException(
                    status_code=403, detail="Раздел «Отсутствия» не доступен вашей роли",
                )

    _check_dates(payload.date_from, payload.date_to)

    a = UserAbsence(
        user_id=str(target_id),
        type=payload.type,
        date_from=payload.date_from,
        date_to=payload.date_to,
        comment=(payload.comment or "").strip() or None,
        created_by=str(user.id),
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return await _to_resp(db, a)


@router.patch("/{absence_id}", response_model=AbsenceResponse)
async def patch_absence(
    absence_id: str,
    payload: AbsencePatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Правка записи. Свою — сам владелец; чужую — админ."""
    a = (await db.execute(
        select(UserAbsence).where(UserAbsence.id == str(absence_id))
    )).scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    is_owner = str(a.user_id) == str(user.id)
    if not is_owner and not await _is_admin(db, request, user):
        raise HTTPException(status_code=403, detail="Нет прав на правку чужой записи")

    data = payload.model_dump(exclude_unset=True)
    if "type" in data:
        a.type = data["type"]
    if "date_from" in data and data["date_from"] is not None:
        a.date_from = data["date_from"]
    if "date_to" in data and data["date_to"] is not None:
        a.date_to = data["date_to"]
    _check_dates(a.date_from, a.date_to)
    if "comment" in data:
        a.comment = (data["comment"] or "").strip() or None

    await db.commit()
    await db.refresh(a)
    return await _to_resp(db, a)


@router.delete("/{absence_id}")
async def delete_absence(
    absence_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить. Свою — владелец, чужую — админ."""
    a = (await db.execute(
        select(UserAbsence).where(UserAbsence.id == str(absence_id))
    )).scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    is_owner = str(a.user_id) == str(user.id)
    if not is_owner and not await _is_admin(db, request, user):
        raise HTTPException(status_code=403, detail="Нет прав на удаление")

    await db.delete(a)
    await db.commit()
    return {"ok": True}
