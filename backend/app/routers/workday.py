"""Workday API — учёт рабочего времени (MVP).

Личные эндпоинты (любой авторизованный, с дополнительной проверкой,
что у его роли включён флаг `track_work_time`):
- GET  /workday/active     — текущая активная сессия + конфиг роли
- POST /workday/start      — начать рабочий день (идемпотентно)
- POST /workday/end        — закончить (manual или idle)
- POST /workday/heartbeat  — обновить last_activity_at

Серверный «ленивый» авто-close: при GET /active, если сессия активна
и `now - last_activity_at > idle_timeout` — закрываем сессию как idle
(ended_at = last_activity_at). Это страховка на случай, если фронт
просто умер (закрыт браузер и т.д.).

Раздел `workday_admin` гейтит просмотр чужих сессий (статистика —
phase 3, эндпоинты пока не реализованы)."""
from __future__ import annotations

from datetime import date as date_cls, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Role, User, WorkSession
from app.schemas.workday import (
    DEFAULT_IDLE_TIMEOUT_MINUTES,
    WorkdayActiveResponse,
    WorkdayBucket,
    WorkdayEndRequest,
    WorkdayGridItem,
    WorkdayHeartbeatResponse,
    WorkdayListItem,
    WorkdaySessionPatch,
    WorkdayStartRequest,
    WorkdayStatsResponse,
    WorkSessionResponse,
)
from app.services.event_outbox import emit_event_safe
from app.services.permissions import get_section_acl, is_superuser


router = APIRouter()


# ---- helpers ---------------------------------------------------------------

def _utcnow() -> datetime:
    """Текущее UTC, **tz-aware**.

    Раньше тут был `datetime.utcnow()` (naive) — Pydantic сериализовал
    без `Z`, фронт `new Date(naive_iso)` интерпретировал как локальное
    время и счётчик стартовал с offset'а (например, с 03:00:00 в МСК).
    `datetime.now(timezone.utc)` → ISO с `+00:00` → браузер сам приведёт
    к локальному корректно."""
    return datetime.now(timezone.utc)


def _to_response(s: WorkSession) -> WorkSessionResponse:
    return WorkSessionResponse(
        id=str(s.id),
        user_id=str(s.user_id),
        started_at=s.started_at,
        ended_at=s.ended_at,
        ended_reason=s.ended_reason,
        last_activity_at=s.last_activity_at,
        note_start=s.note_start,
        note_end=s.note_end,
        duration_seconds=s.duration_seconds,
        is_active=s.is_active,
    )


async def _get_role(db: AsyncSession, user: User) -> Optional[Role]:
    if not user.role_id:
        return None
    return (await db.execute(
        select(Role).where(Role.id == str(user.role_id))
    )).scalar_one_or_none()


def _effective_idle_minutes(role: Optional[Role]) -> int:
    if role and role.idle_timeout_minutes:
        try:
            v = int(role.idle_timeout_minutes)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass
    return DEFAULT_IDLE_TIMEOUT_MINUTES


async def _active_session(db: AsyncSession, user_id: str) -> Optional[WorkSession]:
    return (await db.execute(
        select(WorkSession)
        .where(WorkSession.user_id == str(user_id), WorkSession.ended_at.is_(None))
        .order_by(WorkSession.started_at.desc())
        .limit(1)
    )).scalar_one_or_none()


async def _auto_close_if_idle(
    db: AsyncSession,
    session: WorkSession,
    idle_minutes: int,
) -> Optional[WorkSession]:
    """Если сессия «прокисла» — закрываем её серверно. Возвращаем
    закрытую сессию (None — если ничего не делали)."""
    if not session or not session.is_active:
        return None
    cutoff = _utcnow() - timedelta(minutes=idle_minutes)
    # last_activity_at из БД может прийти naive (старые записи) или
    # tz-aware — приведём для сравнения.
    last = session.last_activity_at
    if last is not None and last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    if last and last >= cutoff:
        return None
    session.ended_at = session.last_activity_at or _utcnow()
    session.ended_reason = "idle"
    await db.commit()
    await db.refresh(session)
    return session


async def _sweep_stale_sessions(db: AsyncSession) -> int:
    """Глобально закрывает «протухшие» активные сессии.

    `_auto_close_if_idle` срабатывает только при GET /active самого
    владельца. Если у пользователя сразу закрылся браузер (ни одного
    heartbeat не успело уйти) — сессия висит «активной» бесконечно, и
    на чужой стороне (статистика) показывается как «сейчас работает».
    Этот свип — глобальная страховка: вызывается из read-эндпоинтов
    статистики и закрывает любую сессию, чей last_activity_at старше
    idle-таймаута её роли (ended_at = last_activity_at, причина idle).
    Идемпотентно; в норме закрывать нечего."""
    now = _utcnow()
    rows = (await db.execute(
        select(WorkSession, Role)
        .join(User, User.id == WorkSession.user_id)
        .outerjoin(Role, Role.id == User.role_id)
        .where(WorkSession.ended_at.is_(None))
    )).all()
    closed = 0
    for session, role in rows:
        cutoff = now - timedelta(minutes=_effective_idle_minutes(role))
        last = session.last_activity_at
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last and last >= cutoff:
            continue
        session.ended_at = session.last_activity_at or session.started_at or _utcnow()
        session.ended_reason = "idle"
        closed += 1
    if closed:
        await db.commit()
    return closed


def _ensure_tracking_enabled(role: Optional[Role]):
    if not role or not bool(getattr(role, "track_work_time", False)):
        raise HTTPException(
            status_code=403,
            detail="Учёт рабочего времени не включён для вашей роли",
        )


# МСК фиксированно UTC+3 (DST в РФ отменён в 2011-м, в Москве не вводится).
_MSK_OFFSET = timedelta(hours=3)


def _today_msk_start_utc() -> datetime:
    """Полночь сегодняшнего МСК-дня в UTC (naive, чтобы дружить
    с naive-датами из старых записей SQLite).

    Логика: now_utc + 3h → «момент в МСК как если бы это был UTC» →
    обрезаем до начала суток → отнимаем 3h обратно в UTC."""
    now_utc = datetime.utcnow()
    msk_now = now_utc + _MSK_OFFSET
    msk_midnight = datetime.combine(msk_now.date(), datetime.min.time())
    return msk_midnight - _MSK_OFFSET


async def _worked_today_closed_seconds(db: AsyncSession, user_id: str) -> int:
    """Сумма длительностей ЗАКРЫТЫХ сессий, начатых сегодня по МСК.

    Активная сессия НЕ учитывается — её live-вклад добавляет фронт
    (счётчик в чипе обновляется каждую секунду). Это разделение
    нужно, чтобы избежать «прыжков» цифры при поллинге /active."""
    start_utc = _today_msk_start_utc()
    q = await db.execute(
        select(WorkSession).where(
            WorkSession.user_id == str(user_id),
            WorkSession.started_at >= start_utc,
            WorkSession.ended_at.is_not(None),
        )
    )
    return sum(_session_seconds(s) for s in q.scalars().all())


# ---- endpoints -------------------------------------------------------------

@router.get("/active", response_model=WorkdayActiveResponse)
async def get_active(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Текущее состояние трекера для меня.

    Идёт первой при загрузке приложения: FE по `session is None` решает
    показать ли блокирующий модал. Если роль не учитывает рабочее время
    (`track_work_time = False`) — модал не показывается вовсе."""
    role = await _get_role(db, user)
    idle_minutes = _effective_idle_minutes(role)
    track = bool(role and getattr(role, "track_work_time", False))

    session = await _active_session(db, str(user.id))
    if session:
        closed = await _auto_close_if_idle(db, session, idle_minutes)
        if closed is not None:
            # стало неактивно — FE покажет модал заново
            session = None

    # Сумма закрытых сессий за сегодня (МСК). Активная не входит —
    # её live-долю прибавляет фронт каждую секунду.
    worked_today = await _worked_today_closed_seconds(db, str(user.id))

    return WorkdayActiveResponse(
        session=_to_response(session) if session else None,
        track_work_time=track,
        idle_timeout_minutes=idle_minutes,
        worked_today_seconds=worked_today,
    )


@router.post("/start", response_model=WorkSessionResponse)
async def start_workday(
    payload: WorkdayStartRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Начать рабочий день. Идемпотентно: если активная сессия уже есть,
    возвращаем её (не создаём дубль). Защищено флагом `track_work_time`
    на роли — для customer/admin без флага получим 403."""
    role = await _get_role(db, user)
    _ensure_tracking_enabled(role)

    existing = await _active_session(db, str(user.id))
    if existing:
        return _to_response(existing)

    now = _utcnow()
    note = (payload.note_start or "").strip() or None
    s = WorkSession(
        user_id=str(user.id),
        started_at=now,
        last_activity_at=now,
        note_start=note,
    )
    db.add(s)
    await db.flush()
    await emit_event_safe(
        db,
        event_type="work_session.after_start",
        entity_type="work_session",
        entity_id=str(s.id),
        payload={
            "id": str(s.id),
            "user_id": str(user.id),
            "started_at": now.isoformat() if hasattr(now, "isoformat") else str(now),
            "note": note,
        },
        payload_version=1,
    )
    await db.commit()
    await db.refresh(s)
    return _to_response(s)


@router.post("/end", response_model=WorkSessionResponse)
async def end_workday(
    payload: WorkdayEndRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Закончить активную сессию.

    `reason='manual'` — кнопка в топбаре, `ended_at = now`.
    `reason='idle'`   — фронт сам закрыл, `ended_at` передаётся клиентом
                        (точное время последней активности)."""
    role = await _get_role(db, user)
    # Не блокируем по track_work_time здесь: если флаг недавно
    # выключили, дай дозакрыть незакрытую сессию.

    session = await _active_session(db, str(user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Активная сессия не найдена")

    now = _utcnow()  # tz-aware
    if payload.reason == "idle":
        # Берём время от клиента, но не позже now, и не раньше started_at.
        client_ts = payload.ended_at or session.last_activity_at or now
        # Все три участника сравнения приводим к tz-aware UTC,
        # иначе Python кидает TypeError на mix naive/aware.
        def _aware(dt):
            if dt is None:
                return None
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        client_aware = _aware(client_ts)
        started_aware = _aware(session.started_at)
        ended = max(started_aware, min(client_aware, now))
        session.ended_at = ended
        session.ended_reason = "idle"
    else:
        session.ended_at = now
        session.ended_reason = "manual"
        session.last_activity_at = now

    note = (payload.note_end or "").strip() or None
    if note:
        session.note_end = note

    # Считаем длительность для analytics. ended_at — tz-aware.
    try:
        duration_seconds = int((session.ended_at - session.started_at).total_seconds()) if session.ended_at and session.started_at else None
    except Exception:
        duration_seconds = None
    await emit_event_safe(
        db,
        event_type="work_session.after_stop",
        entity_type="work_session",
        entity_id=str(session.id),
        payload={
            "id": str(session.id),
            "user_id": str(user.id),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "ended_reason": session.ended_reason,
            "duration_seconds": duration_seconds,
            "note_start": session.note_start,
            "note_end": session.note_end,
        },
        payload_version=1,
    )

    await db.commit()
    await db.refresh(session)
    return _to_response(session)


@router.post("/heartbeat", response_model=WorkdayHeartbeatResponse)
async def heartbeat(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обновить last_activity_at у активной сессии. Шлётся фронтом
    раз в ~60с пока вкладка активна и пользователь что-то делает.
    Возвращает обновлённое время; null если сессии нет."""
    session = await _active_session(db, str(user.id))
    if not session:
        return WorkdayHeartbeatResponse(session_id=None, last_activity_at=None)
    session.last_activity_at = _utcnow()
    await db.commit()
    await db.refresh(session)
    return WorkdayHeartbeatResponse(
        session_id=str(session.id),
        last_activity_at=session.last_activity_at,
    )


# ---- Stats endpoints (phase 3) -------------------------------------------

def _normalize_dt(dt):
    """Naive ↔ aware: приводим к naive UTC для сравнений с БД-naive."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _parse_date(value: Optional[str], default: date_cls) -> date_cls:
    if not value:
        return default
    try:
        return date_cls.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return default


def _date_range(from_str: Optional[str], to_str: Optional[str]):
    """[from 00:00 UTC, to+1 00:00 UTC) — полуоткрытый интервал.
    Дефолт: последние 7 дней (включая сегодня)."""
    today = datetime.utcnow().date()
    end_date = _parse_date(to_str, today)
    start_date = _parse_date(from_str, end_date - timedelta(days=6))
    if start_date > end_date:
        start_date = end_date
    start = datetime.combine(start_date, datetime.min.time())
    end = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    return start_date, end_date, start, end


def _session_seconds(s: WorkSession) -> int:
    """Сколько секунд засчитываем по сессии. Активная — до last_activity_at."""
    if not s or not s.started_at:
        return 0
    end = s.ended_at or s.last_activity_at or s.started_at
    if not end:
        return 0
    return max(0, int((end - s.started_at).total_seconds()))


async def _require_admin_or_self(
    db: AsyncSession,
    request: Request,
    me: User,
    target_user_id: str,
):
    """Свои данные доступны всегда. Чужие — нужен раздел workday_admin."""
    if str(target_user_id) == str(me.id):
        return
    if is_superuser(request):
        return
    acl = await get_section_acl(db, me.role_id, "workday_admin")
    if not acl.can_read:
        raise HTTPException(status_code=403, detail="Нет доступа к чужой статистике")


@router.get("/list", response_model=list[WorkdayListItem])
async def list_users_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
):
    """Сайдбар-фид статистики.

    - `workday_admin` или superuser: список всех юзеров с
      `track_work_time=True` (только тех, кому имеет смысл считать).
    - Без admin-секции: возвращаем только себя (одну строку).

    `total_seconds` считается по сессиям внутри [from, to+1) UTC.
    `has_active` — есть ли сейчас открытая сессия."""
    _, _, start, end = _date_range(from_, to)
    # Страховка: закрываем «протухшие» активные сессии перед чтением.
    await _sweep_stale_sessions(db)
    acl = await get_section_acl(db, user.role_id, "workday_admin")
    is_admin = is_superuser(request) or acl.can_read

    if is_admin:
        # все юзеры с включённым учётом времени
        users_q = await db.execute(
            select(User, Role)
            .outerjoin(Role, Role.id == User.role_id)
            .where(Role.track_work_time.is_(True))
            .order_by(User.full_name.asc())
        )
        rows = users_q.all()
        user_records = [(u, r) for (u, r) in rows]
    else:
        role = await _get_role(db, user)
        user_records = [(user, role)]

    user_ids = [str(u.id) for (u, _) in user_records]
    if not user_ids:
        return []

    sessions_q = await db.execute(
        select(WorkSession).where(
            WorkSession.user_id.in_(user_ids),
            WorkSession.started_at >= start,
            WorkSession.started_at < end,
        )
    )
    by_user: dict[str, list[WorkSession]] = {}
    actives: set[str] = set()
    for s in sessions_q.scalars().all():
        by_user.setdefault(str(s.user_id), []).append(s)
        if s.is_active:
            actives.add(str(s.user_id))

    # Активная может стартовать ДО окна — проверим отдельно
    if not actives:
        active_q = await db.execute(
            select(WorkSession.user_id).where(
                WorkSession.user_id.in_(user_ids),
                WorkSession.ended_at.is_(None),
            )
        )
        for (uid,) in active_q.all():
            actives.add(str(uid))

    # «Сегодня» считаем серверным UTC-днём — для бейджа «не был сегодня».
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

    # Если выбранный период не покрывает сегодня — отдельно догрузим
    # сегодняшние сессии (чтобы worked_today был честным независимо от фильтра).
    today_ss_by_user: dict[str, bool] = {}
    if start > today_start or end <= today_start:
        sep_q = await db.execute(
            select(WorkSession.user_id).where(
                WorkSession.user_id.in_(user_ids),
                WorkSession.started_at >= today_start,
            )
        )
        for (uid,) in sep_q.all():
            today_ss_by_user[str(uid)] = True

    out: list[WorkdayListItem] = []
    for (u, r) in user_records:
        uid = str(u.id)
        ss = by_user.get(uid, [])
        total = sum(_session_seconds(s) for s in ss)
        worked_today = (
            today_ss_by_user.get(uid, False)
            or uid in actives
            or any(s.started_at >= today_start for s in ss)
        )
        out.append(WorkdayListItem(
            user_id=uid,
            full_name=getattr(u, "full_name", None),
            email=getattr(u, "email", None),
            role_name=getattr(r, "name", None) if r else None,
            total_seconds=total,
            sessions_count=len(ss),
            has_active=uid in actives,
            worked_today=worked_today,
        ))
    out.sort(key=lambda x: x.total_seconds, reverse=True)
    return out


@router.get("/grid", response_model=list[WorkdayGridItem])
async def workday_grid(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
):
    """Табличный вид: на каждого сотрудника — посуточная разбивка
    отработанных секунд за период.

    Тот же ACL, что у /list: admin (`workday_admin`/superuser) видит
    всех track-юзеров, обычный пользователь — только себя.

    Сессия целиком относится ко дню своего `started_at` (как в
    /stats groupby=day) — без дробления через полночь."""
    _, _, start, end = _date_range(from_, to)
    # Страховка: закрываем «протухшие» активные сессии перед чтением.
    await _sweep_stale_sessions(db)
    acl = await get_section_acl(db, user.role_id, "workday_admin")
    is_admin = is_superuser(request) or acl.can_read

    if is_admin:
        users_q = await db.execute(
            select(User, Role)
            .outerjoin(Role, Role.id == User.role_id)
            .where(Role.track_work_time.is_(True))
            .order_by(User.full_name.asc())
        )
        user_records = [(u, r) for (u, r) in users_q.all()]
    else:
        role = await _get_role(db, user)
        user_records = [(user, role)]

    user_ids = [str(u.id) for (u, _) in user_records]
    if not user_ids:
        return []

    sessions_q = await db.execute(
        select(WorkSession).where(
            WorkSession.user_id.in_(user_ids),
            WorkSession.started_at >= start,
            WorkSession.started_at < end,
        )
    )
    by_user_days: dict[str, dict[str, int]] = {}
    by_user_total: dict[str, int] = {}
    actives: set[str] = set()
    for s in sessions_q.scalars().all():
        uid = str(s.user_id)
        day = s.started_at.date().isoformat()
        secs = _session_seconds(s)
        d = by_user_days.setdefault(uid, {})
        d[day] = d.get(day, 0) + secs
        by_user_total[uid] = by_user_total.get(uid, 0) + secs
        if s.is_active:
            actives.add(uid)

    # Активная сессия может стартовать ДО окна периода.
    if len(actives) < len(user_ids):
        active_q = await db.execute(
            select(WorkSession.user_id).where(
                WorkSession.user_id.in_(user_ids),
                WorkSession.ended_at.is_(None),
            )
        )
        for (uid,) in active_q.all():
            actives.add(str(uid))

    out: list[WorkdayGridItem] = []
    for (u, r) in user_records:
        uid = str(u.id)
        out.append(WorkdayGridItem(
            user_id=uid,
            full_name=getattr(u, "full_name", None),
            email=getattr(u, "email", None),
            role_name=getattr(r, "name", None) if r else None,
            total_seconds=by_user_total.get(uid, 0),
            has_active=uid in actives,
            days=by_user_days.get(uid, {}),
        ))
    out.sort(key=lambda x: x.total_seconds, reverse=True)
    return out


@router.get("/stats", response_model=WorkdayStatsResponse)
async def user_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    user_id: Optional[str] = Query(None),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    groupby: str = Query("day", pattern="^(day|week|month)$"),
):
    """Детальная статистика по одному пользователю за период.

    `user_id` пуст → данные текущего пользователя. Чужие данные —
    требуют `workday_admin` (или superuser). Возвращаем bucket'ы
    (день / неделя / месяц) с агрегатами и списком сессий внутри."""
    target_id = str(user_id or user.id)
    await _require_admin_or_self(db, request, user, target_id)

    # Страховка: закрываем «протухшие» активные сессии перед чтением.
    await _sweep_stale_sessions(db)
    target_user = (await db.execute(
        select(User).where(User.id == target_id)
    )).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    target_role = await _get_role(db, target_user)

    _, _, start, end = _date_range(from_, to)
    sessions_q = await db.execute(
        select(WorkSession).where(
            WorkSession.user_id == target_id,
            WorkSession.started_at >= start,
            WorkSession.started_at < end,
        ).order_by(WorkSession.started_at.asc())
    )
    sessions = sessions_q.scalars().all()

    # Бакетирование
    buckets_map: dict[str, WorkdayBucket] = {}
    for s in sessions:
        d = s.started_at.date()
        if groupby == "day":
            key = d.isoformat()
            label = d.strftime("%d.%m.%Y")
        elif groupby == "week":
            iso_year, iso_week, _ = d.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            label = f"Неделя {iso_week}, {iso_year}"
        else:  # month
            key = f"{d.year}-{d.month:02d}"
            label = d.strftime("%B %Y")

        bucket = buckets_map.get(key)
        if not bucket:
            bucket = WorkdayBucket(key=key, label=label, total_seconds=0, sessions=[])
            buckets_map[key] = bucket
        bucket.total_seconds += _session_seconds(s)
        bucket.sessions.append(_to_response(s))

    buckets = sorted(buckets_map.values(), key=lambda b: b.key, reverse=True)
    total = sum(b.total_seconds for b in buckets)

    return WorkdayStatsResponse(
        user_id=target_id,
        full_name=getattr(target_user, "full_name", None),
        email=getattr(target_user, "email", None),
        role_name=getattr(target_role, "name", None) if target_role else None,
        total_seconds=total,
        sessions_count=len(sessions),
        buckets=buckets,
    )


@router.patch("/{session_id}", response_model=WorkSessionResponse)
async def admin_patch_session(
    session_id: str,
    payload: WorkdaySessionPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Админская правка существующей сессии. Требует `workday_admin`
    (или superuser). Используется когда сотрудник забыл начать/закончить
    и тимлид хочет внести корректные часы задним числом."""
    if not is_superuser(request):
        acl = await get_section_acl(db, user.role_id, "workday_admin")
        if not acl.can_read:
            raise HTTPException(status_code=403, detail="Нет прав на правку сессий")

    session = (await db.execute(
        select(WorkSession).where(WorkSession.id == str(session_id))
    )).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    data = payload.dict(exclude_unset=True)
    if "started_at" in data and data["started_at"] is not None:
        session.started_at = _normalize_dt(data["started_at"])
    if "ended_at" in data:
        session.ended_at = _normalize_dt(data["ended_at"])
        if session.ended_at is None:
            # переоткрываем — также сбрасываем reason
            session.ended_reason = None
    if "ended_reason" in data:
        session.ended_reason = data["ended_reason"] if session.ended_at else None
    elif session.ended_at and not session.ended_reason:
        # если задали ended_at, но не reason — считаем admin-правкой
        session.ended_reason = "admin"
    if "note_start" in data:
        session.note_start = data["note_start"]
    if "note_end" in data:
        session.note_end = data["note_end"]

    # Если ended_at стал, и он < started_at, или > now — поправим в разумные рамки.
    now = datetime.utcnow()
    if session.ended_at and session.ended_at < session.started_at:
        session.ended_at = session.started_at
    if session.ended_at and session.ended_at > now:
        session.ended_at = now
    # last_activity_at синхронизируем с ended_at, если задан
    if session.ended_at:
        session.last_activity_at = session.ended_at

    await db.commit()
    await db.refresh(session)
    return _to_response(session)
