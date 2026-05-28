"""
Task subtasks (checklist) — CRUD endpoints.

Чек-лист пунктов внутри задачи. Гейт по секции `tasks` (как сама
задача), per-task проверка через `_require_task_access` из tasks.py.

Все маршруты живут под /api/v1; mount происходит в main.py.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Task, TaskAssignee, TaskSubtask, TaskWatcher, User
from app.routers.tasks import _require_task_access
from app.schemas.task_subtask import (
    TaskSubtaskCreate,
    TaskSubtaskReorder,
    TaskSubtaskResponse,
    TaskSubtaskUpdate,
)


router = APIRouter()


async def _ensure_user_on_task(db: AsyncSession, task: Task, user_id: Optional[str]) -> None:
    """Если назначаем пункт чек-листа на юзера, которого нет ни в одной
    из 4 ролей задачи (assignee/creator/multi-assignee/watcher) —
    автоматически добавляем как multi-assignee. Иначе он не сможет
    открыть задачу и увидеть свой пункт.

    Тихо игнорируем, если user_id пуст или совпадает с уже привязанным
    в любой роли. Не падаем при UniqueConstraint — на гонке делаем
    rollback partial и продолжаем.
    """
    if not user_id:
        return
    uid = str(user_id)
    if str(task.assigned_to_user_id or "") == uid:
        return
    if str(task.created_by_user_id or "") == uid:
        return

    ta = (await db.execute(
        select(TaskAssignee.user_id)
        .where(TaskAssignee.task_id == str(task.id))
        .where(TaskAssignee.user_id == uid)
        .limit(1)
    )).scalar_one_or_none()
    if ta:
        return

    tw = (await db.execute(
        select(TaskWatcher.user_id)
        .where(TaskWatcher.task_id == str(task.id))
        .where(TaskWatcher.user_id == uid)
        .limit(1)
    )).scalar_one_or_none()
    if tw:
        return

    # Юзер не в составе задачи — добавляем как multi-assignee.
    db.add(TaskAssignee(task_id=str(task.id), user_id=uid))
    try:
        await db.flush()
    except Exception:
        # UniqueConstraint в гонке — пользователь уже добавлен другим
        # запросом. Откатываем savepoint, продолжаем основной flow.
        await db.rollback()


def _serialize(subtask: TaskSubtask) -> TaskSubtaskResponse:
    assignee = subtask.__dict__.get("assignee")
    return TaskSubtaskResponse(
        id=str(subtask.id),
        task_id=str(subtask.task_id),
        title=subtask.title,
        is_done=bool(subtask.is_done),
        is_urgent=bool(getattr(subtask, "is_urgent", False)),
        assigned_to_user_id=str(subtask.assigned_to_user_id) if subtask.assigned_to_user_id else None,
        assignee_name=getattr(assignee, "full_name", None),
        due_date=subtask.due_date,
        due_time=getattr(subtask, "due_time", None),
        sort_order=int(subtask.sort_order or 0),
        created_by_user_id=str(subtask.created_by_user_id) if subtask.created_by_user_id else None,
        created_at=subtask.created_at,
        updated_at=subtask.updated_at,
        done_at=subtask.done_at,
    )


async def _load_subtask(db: AsyncSession, subtask_id: str) -> Optional[TaskSubtask]:
    res = await db.execute(
        select(TaskSubtask)
        .where(TaskSubtask.id == subtask_id)
        .options(joinedload(TaskSubtask.assignee))
    )
    return res.scalar_one_or_none()


@router.get("/tasks/{task_id}/subtasks", response_model=List[TaskSubtaskResponse])
async def list_subtasks(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    rows = await db.execute(
        select(TaskSubtask)
        .where(TaskSubtask.task_id == str(task.id))
        .options(joinedload(TaskSubtask.assignee))
        .order_by(TaskSubtask.sort_order.asc(), TaskSubtask.created_at.asc())
    )
    return [_serialize(s) for s in rows.scalars().all()]


@router.post("/tasks/{task_id}/subtasks", response_model=TaskSubtaskResponse)
async def create_subtask(
    task_id: str,
    payload: TaskSubtaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    # Сразу вычисляем следующий sort_order. Без транзакционной защиты
    # допускаем редкие коллизии при гонке — ребалансируем на reorder.
    max_order = (
        await db.execute(
            select(func.coalesce(func.max(TaskSubtask.sort_order), -1)).where(
                TaskSubtask.task_id == str(task.id)
            )
        )
    ).scalar_one()
    assignee_id = str(payload.assigned_to_user_id) if payload.assigned_to_user_id else None
    # due_time: принимаем 'HH:MM' или null. Пустую строку нормализуем в None.
    due_time = (payload.due_time or "").strip() or None
    subtask = TaskSubtask(
        task_id=str(task.id),
        title=title,
        is_done=False,
        is_urgent=bool(payload.is_urgent),
        assigned_to_user_id=assignee_id,
        due_date=payload.due_date,
        due_time=due_time,
        sort_order=int(max_order or 0) + 1,
        created_by_user_id=str(user.id),
    )
    db.add(subtask)
    # Если назначили ответственным юзера, которого нет в задаче —
    # автоматически добавляем как соисполнителя (иначе он не сможет
    # увидеть задачу/чек-лист).
    await _ensure_user_on_task(db, task, assignee_id)
    await db.commit()
    await db.refresh(subtask)

    # Reload с joinedload, чтобы в ответе сразу был assignee_name.
    loaded = await _load_subtask(db, str(subtask.id))
    return _serialize(loaded or subtask)


@router.patch("/tasks/subtasks/{subtask_id}", response_model=TaskSubtaskResponse)
async def update_subtask(
    subtask_id: str,
    payload: TaskSubtaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    subtask = await _load_subtask(db, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    task = await Task.get_by_id(db, subtask.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        subtask.title = title

    if payload.is_done is not None:
        new_done = bool(payload.is_done)
        # done_at — серверное время перехода в выполнено. Если снимают
        # галочку — обнуляем done_at, чтобы прошлая дата не вводила в
        # заблуждение.
        if new_done and not subtask.is_done:
            subtask.done_at = datetime.utcnow()
        elif not new_done and subtask.is_done:
            subtask.done_at = None
        subtask.is_done = new_done

    if payload.assigned_to_user_id is not None:
        # Пустая строка/None трактуем как «сбросить ответственного».
        val = str(payload.assigned_to_user_id).strip() if payload.assigned_to_user_id else ""
        subtask.assigned_to_user_id = val or None
        # При смене ответственного — гарантируем, что юзер видит задачу.
        if val:
            await _ensure_user_on_task(db, task, val)

    if payload.due_date is not None:
        subtask.due_date = payload.due_date

    if payload.due_time is not None:
        # Пустая строка = «снять время».
        val = (payload.due_time or "").strip()
        subtask.due_time = val or None

    if payload.is_urgent is not None:
        subtask.is_urgent = bool(payload.is_urgent)

    await db.commit()
    await db.refresh(subtask)
    loaded = await _load_subtask(db, str(subtask.id))
    return _serialize(loaded or subtask)


@router.delete("/tasks/subtasks/{subtask_id}")
async def delete_subtask(
    subtask_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    subtask = await _load_subtask(db, subtask_id)
    if not subtask:
        # Идемпотентно — повторный DELETE не падает.
        return {"deleted": True}
    task = await Task.get_by_id(db, subtask.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    await db.delete(subtask)
    await db.commit()
    return {"deleted": True}


@router.post("/tasks/{task_id}/subtasks/reorder", response_model=List[TaskSubtaskResponse])
async def reorder_subtasks(
    task_id: str,
    payload: TaskSubtaskReorder,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Перепростановка порядка пунктов чек-листа.

    Клиент шлёт полный массив id-шников в нужном порядке. Бэк ставит
    `sort_order = индекс_в_массиве` для каждого пункта, принадлежащего
    задаче. Пункты не из массива (если есть) трогаем минимально —
    оставляем как есть, чтобы потеряных не было.
    """
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    ids = list(payload.ids or [])
    if not ids:
        # Ничего двигать — просто вернём текущий список.
        rows = await db.execute(
            select(TaskSubtask)
            .where(TaskSubtask.task_id == str(task.id))
            .options(joinedload(TaskSubtask.assignee))
            .order_by(TaskSubtask.sort_order.asc(), TaskSubtask.created_at.asc())
        )
        return [_serialize(s) for s in rows.scalars().all()]

    rows = await db.execute(
        select(TaskSubtask).where(TaskSubtask.task_id == str(task.id))
    )
    items = {str(s.id): s for s in rows.scalars().all()}
    for idx, sid in enumerate(ids):
        s = items.get(str(sid))
        if s is not None:
            s.sort_order = idx
    await db.commit()

    rows = await db.execute(
        select(TaskSubtask)
        .where(TaskSubtask.task_id == str(task.id))
        .options(joinedload(TaskSubtask.assignee))
        .order_by(TaskSubtask.sort_order.asc(), TaskSubtask.created_at.asc())
    )
    return [_serialize(s) for s in rows.scalars().all()]
