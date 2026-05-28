"""Profiles API — расширенная карточка сотрудника.

Эндпоинты:
- GET    /profiles/me                — мой профиль (создаётся при первом обращении)
- PATCH  /profiles/me                — править личные поля своего профиля
- GET    /profiles/suggest           — автокомплит чипов (skills/interests)
- GET    /profiles/{user_id}         — чужой профиль (видят все авторизованные)
- PATCH  /profiles/{user_id}         — править чужой профиль (нужен users.edit_all)

Все авторизованные пользователи видят все профили (publicly readable).
Формальные поля (job_title/department/manager_id/hire_date) правит только
админ — определяется как `users.edit_all` (или superuser). Личные поля —
сам владелец + админ.

Если `birth_show_year=False` — бэк отдаёт `birth_date` с занулённым годом
(`1900-MM-DD`) в выдаче для всех, кто не сам владелец и не админ. Это
проще, чем городить отдельное поле — фронт показывает только день/месяц,
если год < 1901.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Role, User, UserProfile
from app.schemas.profile import (
    UserProfileResponse,
    UserProfilePatchSelf,
    UserProfilePatchAdmin,
)
from app.services.permissions import get_section_acl, is_superuser


router = APIRouter()


# Год-«пустышка», подмешивается когда пользователь скрыл год рождения.
# Фронт по `year < 1901` решает показать только день/месяц.
_HIDDEN_YEAR = 1900


# ---- helpers -------------------------------------------------------------

async def _is_admin(db: AsyncSession, request: Request, me: User) -> bool:
    """Админ для целей правки чужого профиля.

    Критерий — `users.edit_all` (т.е. кто и так управляет учётками)
    либо системный superuser."""
    if is_superuser(request):
        return True
    acl = await get_section_acl(db, me.role_id, "users")
    return bool(acl.edit_all)


async def _get_or_create_profile(db: AsyncSession, user_id: str) -> UserProfile:
    p = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == str(user_id))
    )).scalar_one_or_none()
    if p:
        return p
    p = UserProfile(user_id=str(user_id), interests=[], skills=[])
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def _fetch_role_name(db: AsyncSession, role_id: Optional[str]) -> Optional[str]:
    if not role_id:
        return None
    res = await db.execute(select(Role.name).where(Role.id == str(role_id)))
    row = res.scalar_one_or_none()
    return row


async def _fetch_user_brief(db: AsyncSession, user_id: Optional[str]):
    if not user_id:
        return None
    res = await db.execute(
        select(User.id, User.full_name, User.email, User.avatar_url, User.role_id)
        .where(User.id == str(user_id))
    )
    return res.first()


async def _build_response(
    db: AsyncSession,
    profile: UserProfile,
    *,
    hide_birth_year: bool,
) -> UserProfileResponse:
    user_row = await _fetch_user_brief(db, profile.user_id)
    role_name = None
    if user_row and user_row.role_id:
        role_name = await _fetch_role_name(db, user_row.role_id)
    manager_name = None
    if profile.manager_id:
        mrow = await _fetch_user_brief(db, profile.manager_id)
        manager_name = mrow.full_name if mrow else None

    birth = profile.birth_date
    show_year = bool(profile.birth_show_year)
    if hide_birth_year and birth and not show_year:
        # Подменяем год на «пустышку» — фронт распознает по year<1901.
        try:
            birth = date(_HIDDEN_YEAR, birth.month, birth.day)
        except ValueError:
            birth = None

    return UserProfileResponse(
        user_id=str(profile.user_id),
        job_title=profile.job_title,
        department=profile.department,
        manager_id=profile.manager_id,
        hire_date=profile.hire_date,
        birth_date=birth,
        birth_show_year=show_year,
        bio=profile.bio,
        interests=list(profile.interests or []),
        skills=list(profile.skills or []),
        telegram_username=profile.telegram_username,
        full_name=user_row.full_name if user_row else None,
        email=user_row.email if user_row else None,
        avatar_url=user_row.avatar_url if user_row else None,
        role_name=role_name,
        manager_full_name=manager_name,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _normalize_chip_list(values) -> list[str]:
    """Чистим список чипов: trim, выкидываем пустые, дедуп без сортировки,
    ограничиваем длину одного элемента 64 символами."""
    out: list[str] = []
    seen: set[str] = set()
    for v in (values or []):
        s = str(v).strip()
        if not s:
            continue
        s = s[:64]
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    # Ограничим суммарный размер списка, чтобы не было перегруза.
    return out[:50]


def _apply_self_patch(profile: UserProfile, patch: UserProfilePatchSelf) -> None:
    data = patch.model_dump(exclude_unset=True)
    if "birth_date" in data:
        profile.birth_date = data["birth_date"]
    if "birth_show_year" in data:
        profile.birth_show_year = bool(data["birth_show_year"])
    if "bio" in data:
        profile.bio = (data["bio"] or "").strip() or None
    if "interests" in data:
        profile.interests = _normalize_chip_list(data["interests"])
    if "skills" in data:
        profile.skills = _normalize_chip_list(data["skills"])
    if "telegram_username" in data:
        profile.telegram_username = data["telegram_username"] or None


def _apply_admin_patch(profile: UserProfile, patch: UserProfilePatchAdmin) -> None:
    # Сначала «личные» поля общим путём.
    _apply_self_patch(profile, patch)
    data = patch.model_dump(exclude_unset=True)
    if "job_title" in data:
        profile.job_title = (data["job_title"] or "").strip() or None
    if "department" in data:
        profile.department = (data["department"] or "").strip() or None
    if "manager_id" in data:
        profile.manager_id = data["manager_id"] or None
    if "hire_date" in data:
        profile.hire_date = data["hire_date"]


# ---- endpoints -----------------------------------------------------------

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Мой профиль — создаётся пустой при первом обращении."""
    p = await _get_or_create_profile(db, str(user.id))
    return await _build_response(db, p, hide_birth_year=False)


@router.patch("/me", response_model=UserProfileResponse)
async def patch_my_profile(
    payload: UserProfilePatchSelf,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Правка ЛИЧНЫХ полей своего профиля. Формальные поля
    (должность/отдел/руководитель/дата приёма) сюда нельзя — только
    через админский эндпоинт."""
    p = await _get_or_create_profile(db, str(user.id))
    _apply_self_patch(p, payload)
    await db.commit()
    await db.refresh(p)
    return await _build_response(db, p, hide_birth_year=False)


@router.get("/suggest", response_model=List[str])
async def suggest_chips(
    field: str = Query(..., pattern="^(skills|interests)$"),
    q: Optional[str] = Query(None, max_length=64),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),  # noqa: ARG001 — auth gate
):
    """Уникальные значения чипов из всех профилей, опционально
    отфильтрованные по подстроке `q` (без учёта регистра).

    Реализация: тянем колонку JSON у всех профилей, разбираем в Python,
    нормализуем (lower) и считаем частоты. Для текущего объёма данных
    этого достаточно; если профилей станет много — переедем на
    отдельный справочник или denormalized колонку с GIN-индексом."""
    col = UserProfile.skills if field == "skills" else UserProfile.interests
    res = await db.execute(select(col))
    counts: dict[str, tuple[str, int]] = {}
    for (vals,) in res.all():
        if not vals:
            continue
        for raw in vals:
            s = str(raw).strip()
            if not s:
                continue
            key = s.lower()
            label, n = counts.get(key, (s, 0))
            counts[key] = (label, n + 1)
    if q:
        ql = q.strip().lower()
        items = [(label, n) for key, (label, n) in counts.items() if ql in key]
    else:
        items = [(label, n) for (label, n) in counts.values()]
    items.sort(key=lambda x: (-x[1], x[0].lower()))
    return [label for (label, _) in items[:limit]]


@router.get("/birthdays")
async def upcoming_birthdays(
    window: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),  # noqa: ARG001 — auth gate
):
    """Ближайшие дни рождения сотрудников в окне `window` дней.

    Сравнение по дню+месяцу (год игнорируется). Возвращает список,
    отсортированный по близости: сегодня → дальше."""
    from datetime import date as _date

    rows = (await db.execute(
        select(
            UserProfile.user_id,
            UserProfile.birth_date,
            UserProfile.birth_show_year,
            User.full_name,
            User.avatar_url,
        )
        .join(User, User.id == UserProfile.user_id)
        .where(UserProfile.birth_date.is_not(None))
    )).all()

    today = _date.today()
    _MONTHS = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
               "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    out = []
    for (uid, bdate, show_year, full_name, avatar) in rows:
        if not bdate:
            continue
        # bdate может прийти как date или строка — нормализуем.
        if not isinstance(bdate, _date):
            try:
                bdate = _date.fromisoformat(str(bdate)[:10])
            except (ValueError, TypeError):
                continue
        # Ближайшее наступление ДР (в этом или следующем году).
        try:
            nxt = bdate.replace(year=today.year)
        except ValueError:
            # 29 февраля в невисокосный — сдвигаем на 1 марта.
            nxt = _date(today.year, 3, 1)
        if nxt < today:
            try:
                nxt = bdate.replace(year=today.year + 1)
            except ValueError:
                nxt = _date(today.year + 1, 3, 1)
        days_until = (nxt - today).days
        if days_until > window:
            continue
        age = None
        if show_year and bdate.year > 1900:
            age = nxt.year - bdate.year
        out.append({
            "user_id": str(uid),
            "full_name": full_name,
            "avatar_url": avatar,
            "days_until": days_until,
            "is_today": days_until == 0,
            "date_label": f"{bdate.day} {_MONTHS[bdate.month]}",
            "age_turning": age,
        })
    out.sort(key=lambda x: x["days_until"])
    return out


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    user: User = Depends(CurrentUser),
):
    """Профиль другого пользователя — публично для авторизованных.
    Год рождения скрывается, если владелец так настроил, и смотрит
    не админ и не сам владелец."""
    target = (await db.execute(
        select(User).where(User.id == str(user_id))
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    p = await _get_or_create_profile(db, str(user_id))
    am_owner = str(user.id) == str(user_id)
    am_admin = await _is_admin(db, request, user)
    return await _build_response(
        db, p,
        hide_birth_year=not (am_owner or am_admin),
    )


@router.patch("/{user_id}", response_model=UserProfileResponse)
async def patch_user_profile(
    user_id: str,
    payload: UserProfilePatchAdmin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Админская правка любого профиля. Нужен `users.edit_all`
    (или superuser). Если редактируется ЧУЖОЙ профиль без админ-прав —
    403."""
    am_owner = str(user.id) == str(user_id)
    am_admin = await _is_admin(db, request, user)
    if not am_owner and not am_admin:
        raise HTTPException(status_code=403, detail="Нет прав на правку профиля")
    if not am_admin:
        # Свой профиль через этот эндпоинт нельзя — только через /me,
        # чтобы случайно не пролезли формальные поля.
        raise HTTPException(
            status_code=403,
            detail="Личные поля правьте через /profiles/me; формальные — только админ",
        )

    target = (await db.execute(
        select(User).where(User.id == str(user_id))
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if payload.manager_id:
        if payload.manager_id == str(user_id):
            raise HTTPException(
                status_code=400, detail="Сотрудник не может быть своим руководителем",
            )
        exists = (await db.execute(
            select(User.id).where(User.id == str(payload.manager_id))
        )).scalar_one_or_none()
        if not exists:
            raise HTTPException(status_code=400, detail="Руководитель не найден")

    p = await _get_or_create_profile(db, str(user_id))
    _apply_admin_patch(p, payload)
    await db.commit()
    await db.refresh(p)
    return await _build_response(db, p, hide_birth_year=False)
