"""
Tasks API Router
"""
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Body, Request, Response, File, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, func, text

from app.core.config import settings
from app.database.session import get_db
from app.models import Task, TaskUserMatrix, TaskAssignee, TaskWatcher, Deal, Stage, Company, User, IncomeExpenseEntry, PenaltyRule
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskWithRelations
from app.core.auth_middleware import CurrentUser
from app.services.event_log import log_event
from app.services.approval_runtime import ensure_entity_action_allowed
from app.services.permissions import get_section_permissions, ensure_can_edit_record
from app.services.storage import (
    clean_name,
    delete_path,
    ensure_path,
    storage_available,
    upload_file_with_safe_extension,
)
from app.services.upload_security import write_upload_to_tmp

router = APIRouter()

MATRIX_QUADRANTS = {
    "urgent_important",
    "not_urgent_important",
    "urgent_not_important",
    "not_urgent_not_important",
}


class TaskMatrixUpdate(BaseModel):
    quadrant: str
    sort_order: Optional[int] = 0


class TaskMatrixReorder(BaseModel):
    quadrant: str
    task_ids: List[str] = Field(default_factory=list)

async def _sync_task_assignees(db: AsyncSession, task_id: str, ids: Optional[List[str]]) -> None:
    """Replace the full assignee set for a task. `None` means no change."""
    if ids is None:
        return
    await db.execute(delete(TaskAssignee).where(TaskAssignee.task_id == str(task_id)))
    seen = set()
    for uid in ids:
        s = str(uid).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        db.add(TaskAssignee(task_id=str(task_id), user_id=s))
    await db.commit()


async def _sync_task_watchers(db: AsyncSession, task_id: str, ids: Optional[List[str]]) -> Optional[Dict[str, List[str]]]:
    """Replace the full watcher set for a task. `None` means no change.

    Возвращает diff `{added: [...], removed: [...]}` для последующего emit'а
    `task.after_watchers_change` на стороне вызывающего. Если `ids is None`
    (без изменений) — возвращает None.
    """
    if ids is None:
        return None
    prev_rows = await db.execute(
        select(TaskWatcher.user_id).where(TaskWatcher.task_id == str(task_id))
    )
    prev_set = {str(x) for x in prev_rows.scalars().all()}
    await db.execute(delete(TaskWatcher).where(TaskWatcher.task_id == str(task_id)))
    seen = set()
    for uid in ids:
        s = str(uid).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        db.add(TaskWatcher(task_id=str(task_id), user_id=s))
    await db.commit()
    added = sorted(seen - prev_set)
    removed = sorted(prev_set - seen)
    return {"added": added, "removed": removed, "final": sorted(seen)}


async def _load_task_people(db: AsyncSession, task_id: str) -> Dict[str, List[str]]:
    a = await db.execute(select(TaskAssignee.user_id).where(TaskAssignee.task_id == str(task_id)))
    w = await db.execute(select(TaskWatcher.user_id).where(TaskWatcher.task_id == str(task_id)))
    return {
        "assignee_ids": [str(x) for x in a.scalars().all()],
        "watcher_ids": [str(x) for x in w.scalars().all()],
    }


async def _load_task_people_batch(db: AsyncSession, task_ids: List[str]) -> Dict[str, Dict[str, List[str]]]:
    """Batch load assignee/watcher ids for many tasks at once."""
    if not task_ids:
        return {}
    ids = [str(t) for t in task_ids if t]
    a_rows = (await db.execute(
        select(TaskAssignee.task_id, TaskAssignee.user_id).where(TaskAssignee.task_id.in_(ids))
    )).all()
    w_rows = (await db.execute(
        select(TaskWatcher.task_id, TaskWatcher.user_id).where(TaskWatcher.task_id.in_(ids))
    )).all()
    out: Dict[str, Dict[str, List[str]]] = {tid: {"assignee_ids": [], "watcher_ids": []} for tid in ids}
    for tid, uid in a_rows:
        out.setdefault(str(tid), {"assignee_ids": [], "watcher_ids": []})["assignee_ids"].append(str(uid))
    for tid, uid in w_rows:
        out.setdefault(str(tid), {"assignee_ids": [], "watcher_ids": []})["watcher_ids"].append(str(uid))
    return out


def _resolve_assignee_set(task_payload) -> Optional[List[str]]:
    """Return the desired assignee list (or None for "do not touch").
    - If `assignee_ids` is explicitly provided — use it as the full set.
    - Otherwise, if `assigned_to_user_id` is present — fall back to [that one].
    """
    ids = getattr(task_payload, "assignee_ids", None)
    if ids is not None:
        return [str(x) for x in ids]
    primary = getattr(task_payload, "assigned_to_user_id", None)
    if primary:
        return [str(primary)]
    return None


def _parse_uuid(value: Optional[str], field_name: str) -> Optional[uuid.UUID]:
    if value is None:
        return None
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")

def _to_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None

def _plan_date_from_due(due_date_value) -> Optional[date]:
    due_date = _to_date(due_date_value)
    if not due_date:
        return None
    return due_date + timedelta(days=14)


def _default_matrix_quadrant(task: Task) -> str:
    due_date = _to_date(getattr(task, "due_date", None))
    priority = str(getattr(task, "priority", "") or "normal")
    is_urgent = bool(due_date and due_date <= date.today())
    is_important = priority in {"high", "urgent"}
    if is_urgent and is_important:
        return "urgent_important"
    if is_important:
        return "not_urgent_important"
    if is_urgent:
        return "urgent_not_important"
    return "not_urgent_not_important"


async def _get_user_matrix_map(db: AsyncSession, user_id: str, task_ids: List[str]) -> Dict[str, TaskUserMatrix]:
    if not task_ids:
        return {}
    result = await db.execute(
        select(TaskUserMatrix)
        .where(TaskUserMatrix.user_id == str(user_id))
        .where(TaskUserMatrix.task_id.in_([str(item) for item in task_ids]))
    )
    return {str(item.task_id): item for item in result.scalars().all()}


def _apply_matrix_fields(task_dict: Dict[str, Any], task: Task, matrix_map: Dict[str, TaskUserMatrix]) -> Dict[str, Any]:
    position = matrix_map.get(str(task.id))
    task_dict["matrix_quadrant"] = position.quadrant if position else _default_matrix_quadrant(task)
    task_dict["matrix_sort_order"] = int(position.sort_order or 0) if position else None
    task_dict["matrix_manual"] = bool(position)
    return task_dict


def _sanitize_task_attachments(value: Optional[List[Any]]) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized_items: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, str):
            path = item.strip()
            if not path:
                continue
            normalized_items.append(
                {
                    "name": path.replace("\\", "/").rsplit("/", 1)[-1] or "Файл",
                    "path": path,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        name = str(item.get("name") or "").strip()
        if not name:
            name = path.replace("\\", "/").rsplit("/", 1)[-1] if path else "Файл"
        attachment: Dict[str, Any] = {"name": name or "Файл"}
        if path:
            attachment["path"] = path
        size = item.get("size")
        if isinstance(size, (int, float)):
            attachment["size"] = int(size)
        content_type = str(item.get("content_type") or "").strip()
        if content_type:
            attachment["content_type"] = content_type
        normalized_items.append(attachment)
    return normalized_items


async def _require_task_access(db: AsyncSession, user: User, task: Task) -> None:
    """Проверить что пользователь может ЧИТАТЬ конкретную задачу.

    Пользователь со `read_all` видит всё. Со `read_assigned` видит задачи где
    он связан в любой из 4 ролей:
      • main assignee (legacy `assigned_to_user_id`);
      • постановщик (`created_by_user_id`);
      • multi-assignee (`task_assignees` table);
      • watcher (`task_watchers` table).

    Без read_assigned — 404 (как и было). Раньше учитывалось ТОЛЬКО
    `assigned_to_user_id` — постановщик/multi-assignee получали 404 на
    свою же задачу.
    """
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
    if read_all:
        return
    if not read_assigned:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    uid = str(user.id)
    # 1) main assignee or postановщик — это on the Task row, без доп. запросов.
    if str(task.assigned_to_user_id) == uid or str(task.created_by_user_id) == uid:
        return
    # 2) multi-assignee
    ta = (await db.execute(
        select(TaskAssignee.user_id)
        .where(TaskAssignee.task_id == str(task.id))
        .where(TaskAssignee.user_id == uid)
        .limit(1)
    )).scalar_one_or_none()
    if ta:
        return
    # 3) watcher
    tw = (await db.execute(
        select(TaskWatcher.user_id)
        .where(TaskWatcher.task_id == str(task.id))
        .where(TaskWatcher.user_id == uid)
        .limit(1)
    )).scalar_one_or_none()
    if tw:
        return
    raise HTTPException(status_code=404, detail="Задача не найдена")


def _serialize_task(task: Task) -> Dict[str, Any]:
    return {
        "id": str(task.id) if task.id else None,
        "number": task.number,
        "title": task.title,
        "description": task.description,
        "deal_id": str(task.deal_id) if task.deal_id else None,
        "stage_id": str(task.stage_id) if task.stage_id else None,
        "status": task.status,
        "priority": task.priority,
        "assigned_to_id": str(task.assigned_to_id) if task.assigned_to_id else None,
        "created_by_id": str(task.created_by_id) if task.created_by_id else None,
        "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
        "created_by_user_id": str(task.created_by_user_id) if task.created_by_user_id else None,
        "payer_id": str(task.payer_id) if task.payer_id else None,
        "payee_id": str(task.payee_id) if task.payee_id else None,
        "start_date": task.start_date,
        "due_date": task.due_date,
        "due_time": task.due_time,
        "completed_at": task.completed_at,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "tags": task.tags or [],
        "attachments": _sanitize_task_attachments(task.attachments or []),
        "notify_assigned": task.notify_assigned,
        "notify_overdue": task.notify_overdue,
        "budget": task.budget,
        "category_code": task.category_code,
        "work_category": task.work_category,
        "source_auction_id": str(task.source_auction_id) if task.source_auction_id else None,
        "executor_rating": task.executor_rating,
        "final_budget": task.final_budget,
        "rating_coefficient": task.rating_coefficient,
        "deadline_coefficient": task.deadline_coefficient,
        "penalty_amount": task.penalty_amount,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "deal_title": task.deal.title if getattr(task, "deal", None) else None,
        "stage_name": task.stage.name if getattr(task, "stage", None) else None,
        "assigned_to_name": task.assigned_to.name if getattr(task, "assigned_to", None) else None,
        "created_by_name": task.created_by.name if getattr(task, "created_by", None) else None,
        "assigned_to_user_name": task.assigned_to_user.full_name if getattr(task, "assigned_to_user", None) else None,
        "assigned_to_user_avatar_url": task.assigned_to_user.avatar_url if getattr(task, "assigned_to_user", None) else None,
        "created_by_user_name": task.created_by_user.full_name if getattr(task, "created_by_user", None) else None,
        "created_by_user_avatar_url": task.created_by_user.avatar_url if getattr(task, "created_by_user", None) else None,
        "payer_name": task.payer.name if getattr(task, "payer", None) else None,
        "payee_name": task.payee.name if getattr(task, "payee", None) else None,
    }


async def calculate_penalty_coefficients(db, task, executor_rating: Optional[int] = None):
    """
    Рассчитать коэффициенты штрафов/бонусов для задачи.
    Вызывается при завершении задачи.
    """
    if not task.budget or task.budget <= 0:
        return None, None, None, None
    
    rating = executor_rating if executor_rating else task.executor_rating
    if not rating:
        return None, None, None, None
    
    # Получаем правила
    rating_rules = await PenaltyRule.get_by_type(db, "rating", only_active=True)
    deadline_rules = await PenaltyRule.get_by_type(db, "deadline", only_active=True)
    
    # Коэффициент за оценку
    rating_coef = 1.0
    for rule in rating_rules:
        if rule.condition_min <= rating <= rule.condition_max:
            rating_coef = rule.coefficient
            break
    
    # Коэффициент за сроки
    deadline_coef = 1.0
    if task.start_date and task.due_date and task.completed_at:
        planned_duration = (task.due_date - task.start_date).days
        if planned_duration > 0:
            completed_date = task.completed_at.date() if hasattr(task.completed_at, 'date') else task.completed_at
            actual_duration = (completed_date - task.start_date).days
            deviation_percent = ((actual_duration - planned_duration) / planned_duration) * 100
            
            for rule in deadline_rules:
                if rule.condition_min <= deviation_percent <= rule.condition_max:
                    deadline_coef = rule.coefficient
                    break
    
    # Расчёт итогового бюджета
    final_budget = task.budget * rating_coef * deadline_coef
    penalty_amount = task.budget - final_budget
    
    return rating_coef, deadline_coef, final_budget, penalty_amount


@router.get("/", response_model=List[TaskWithRelations])
async def get_tasks(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    deal_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_code: Optional[str] = None,
    work_category: Optional[str] = None,
    source: Optional[str] = None,  # 'auction' | 'manual'
    has_budget: Optional[bool] = None,
    overdue: Optional[bool] = None,
    search: Optional[str] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Получить список всех задач с фильтрами. Возвращает заголовок X-Total-Count."""
    try:
        from sqlalchemy.orm import joinedload
        base_query = select(Task)
        query = select(Task).options(
            joinedload(Task.deal),
            joinedload(Task.stage),
            joinedload(Task.assigned_to),
            joinedload(Task.created_by),
            joinedload(Task.assigned_to_user),
            joinedload(Task.created_by_user),
            joinedload(Task.payer),
            joinedload(Task.payee)
        )

        deal_uuid = _parse_uuid(deal_id, "deal_id") if deal_id else None
        assigned_uuid = _parse_uuid(assigned_to_id, "assigned_to_id") if assigned_to_id else None

        def apply_filters(q):
            if deal_uuid:
                q = q.where(Task.deal_id == deal_uuid)
            if assigned_uuid:
                q = q.where(Task.assigned_to_id == assigned_uuid)
            if assigned_to_user_id:
                # Фильтр «по ответственному» — учитываем и legacy single-
                # assignee (`Task.assigned_to_user_id`), и multi-assignees
                # из `TaskAssignee`. Иначе при добавлении нескольких
                # ответственных фильтр в UI «пустеет» — никто не находится.
                assigned_user_uuid = _parse_uuid(assigned_to_user_id, "assigned_to_user_id")
                assignee_subq = select(TaskAssignee.task_id).where(
                    TaskAssignee.user_id == str(assigned_user_uuid)
                )
                q = q.where(or_(
                    Task.assigned_to_user_id == assigned_user_uuid,
                    Task.id.in_(assignee_subq),
                ))
            if status:
                q = q.where(Task.status == status)
            if priority:
                q = q.where(Task.priority == priority)
            if category_code:
                q = q.where(Task.category_code == category_code)
            if work_category:
                q = q.where(Task.work_category == work_category)
            if source == 'auction':
                q = q.where(Task.source_auction_id.isnot(None))
            elif source == 'manual':
                q = q.where(Task.source_auction_id.is_(None))
            if has_budget is True:
                q = q.where(Task.budget.isnot(None)).where(Task.budget > 0)
            elif has_budget is False:
                q = q.where(or_(Task.budget.is_(None), Task.budget == 0))
            if overdue is True:
                today = date.today()
                q = q.where(Task.due_date.isnot(None)).where(Task.due_date < today).where(Task.status.notin_(['completed', 'cancelled']))
            if search:
                like = f"%{search.strip()}%"
                q = q.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
            if due_date_from:
                parsed_from = _to_date(due_date_from)
                if parsed_from:
                    q = q.where(Task.due_date >= parsed_from)
            if due_date_to:
                parsed_to = _to_date(due_date_to)
                if parsed_to:
                    q = q.where(Task.due_date <= parsed_to)
            return q

        query = apply_filters(query)
        base_query = apply_filters(base_query)

        read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
        if not read_all:
            if not read_assigned:
                response.headers["X-Total-Count"] = "0"
                return []
            # «Свои» задачи = где user в любой из 4 ролей: main assignee,
            # постановщик, multi-assignee (TaskAssignee), watcher (TaskWatcher).
            # Раньше учитывалось только assigned_to_user_id — постановщики
            # и multi-assignees получали пустой список.
            uid = str(user.id)
            ta_subq = select(TaskAssignee.task_id).where(TaskAssignee.user_id == uid)
            tw_subq = select(TaskWatcher.task_id).where(TaskWatcher.user_id == uid)
            access_filter = or_(
                Task.assigned_to_user_id == uid,
                Task.created_by_user_id == uid,
                Task.id.in_(ta_subq),
                Task.id.in_(tw_subq),
            )
            query = query.where(access_filter)
            base_query = base_query.where(access_filter)

        # Total count for pagination
        total_q = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(total_q)).scalar_one() or 0
        response.headers["X-Total-Count"] = str(total)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        result = await db.execute(query)
        tasks = result.unique().scalars().all()
        task_ids_list = [str(task.id) for task in tasks]
        matrix_map = await _get_user_matrix_map(db, str(user.id), task_ids_list)
        people_map = await _load_task_people_batch(db, task_ids_list)

        # Формируем ответ с названиями
        response_tasks = []
        for task in tasks:
            people = people_map.get(str(task.id), {"assignee_ids": [], "watcher_ids": []})
            task_dict = {
                "id": str(task.id) if task.id else None,
                "number": task.number,
                "title": task.title,
                "description": task.description,
                "deal_id": str(task.deal_id) if task.deal_id else None,
                "stage_id": str(task.stage_id) if task.stage_id else None,
                "status": task.status,
                "priority": task.priority,
                "assigned_to_id": str(task.assigned_to_id) if task.assigned_to_id else None,
                "created_by_id": str(task.created_by_id) if task.created_by_id else None,
                "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                "created_by_user_id": str(task.created_by_user_id) if task.created_by_user_id else None,
                "payer_id": str(task.payer_id) if task.payer_id else None,
                "payee_id": str(task.payee_id) if task.payee_id else None,
                "start_date": task.start_date,
                "due_date": task.due_date,
                "due_time": task.due_time,
                "completed_at": task.completed_at,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "tags": task.tags or [],
                "attachments": _sanitize_task_attachments(task.attachments or []),
                "notify_assigned": task.notify_assigned,
                "notify_overdue": task.notify_overdue,
                "budget": task.budget,
                "category_code": task.category_code,
                "work_category": task.work_category,
                "source_auction_id": str(task.source_auction_id) if task.source_auction_id else None,
                "executor_rating": task.executor_rating,
                "final_budget": task.final_budget,
                "rating_coefficient": task.rating_coefficient,
                "deadline_coefficient": task.deadline_coefficient,
                "penalty_amount": task.penalty_amount,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "deal_title": task.deal.title if task.deal else None,
                "stage_name": task.stage.name if task.stage else None,
                "assigned_to_name": task.assigned_to.name if task.assigned_to else None,
                "created_by_name": task.created_by.name if task.created_by else None,
                "assigned_to_user_name": task.assigned_to_user.full_name if task.assigned_to_user else None,
                "assigned_to_user_avatar_url": task.assigned_to_user.avatar_url if task.assigned_to_user else None,
                "created_by_user_name": task.created_by_user.full_name if task.created_by_user else None,
                "created_by_user_avatar_url": task.created_by_user.avatar_url if task.created_by_user else None,
                "payer_name": task.payer.name if task.payer else None,
                "payee_name": task.payee.name if task.payee else None,
                "assignee_ids": people["assignee_ids"],
                "watcher_ids": people["watcher_ids"],
            }
            response_tasks.append(_apply_matrix_fields(task_dict, task, matrix_map))

        return response_tasks
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать новую задачу"""
    # Проверяем существование проекта (если указан)
    if task.deal_id:
        deal = await Deal.get_by_id(db, task.deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Проект не найден")

    # Если указан этап, проверяем его существование
    if task.stage_id:
        stage = await Stage.get_by_id(db, task.stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Этап не найден")

    # Проверяем ответственного
    if task.assigned_to_id:
        assigned_to = await Company.get_by_id(db, task.assigned_to_id)
        if not assigned_to:
            raise HTTPException(status_code=404, detail="Ответственный не найден")
    assigned_user = None
    if task.assigned_to_user_id:
        assigned_user = await User.get_by_id(db, task.assigned_to_user_id)
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
    created_user = None
    if task.created_by_user_id:
        created_user = await User.get_by_id(db, task.created_by_user_id)
        if not created_user:
            raise HTTPException(status_code=404, detail="Created user not found")
    # Budget-related validation temporarily disabled — budgeted tasks
    # are not in use yet. The IncomeExpense linkage below only fires when
    # all of (budget, category, payer, payee, due_date) happen to be set.
    if task.budget and task.budget > 0:
        if task.payer_id:
            payer = await Company.get_by_id(db, task.payer_id)
            if not payer:
                raise HTTPException(status_code=404, detail="Payer company not found")
        if task.payee_id:
            payee = await Company.get_by_id(db, task.payee_id)
            if not payee:
                raise HTTPException(status_code=404, detail="Payee company not found")

    # Assign the next sequential human number. MAX(number)+1 is racy
    # under concurrency, so retry on the tasks.number UNIQUE violation —
    # each retry recomputes the max. Bounded so a genuine failure still
    # surfaces instead of looping forever.
    from sqlalchemy import func as sa_func, select as sa_select
    from sqlalchemy.exc import IntegrityError

    task_kwargs = dict(
        title=task.title,
        description=task.description,
        deal_id=task.deal_id or None,  # '' / отсутствие проекта -> NULL (допустимо)
        stage_id=task.stage_id if task.stage_id else None,
        status=task.status,
        priority=task.priority,
        assigned_to_id=task.assigned_to_id if task.assigned_to_id else None,
        created_by_id=task.created_by_id if task.created_by_id else None,
        assigned_to_user_id=str(assigned_user.id) if assigned_user else None,
        created_by_user_id=str(created_user.id) if created_user else None,
        start_date=task.start_date,
        due_date=task.due_date,
        due_time=task.due_time,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        budget=task.budget,
        category_code=task.category_code,
        work_category=task.work_category,
        payer_id=task.payer_id or None,
        payee_id=task.payee_id or None,
        tags=task.tags or [],
        attachments=_sanitize_task_attachments(task.attachments or []),
        notify_assigned=task.notify_assigned,
        notify_overdue=task.notify_overdue,
    )

    # Задача без проекта допустима (deal_id nullable).
    db_task = None
    attempts = max(1, settings.TASK_NUMBER_MAX_RETRIES)
    for attempt in range(attempts):
        next_number_q = await db.execute(
            sa_select(sa_func.coalesce(sa_func.max(Task.number), 0) + 1)
        )
        next_number = int(next_number_q.scalar() or 1)
        try:
            db_task = await Task.create(db, number=next_number, **task_kwargs)
            break
        except IntegrityError as exc:
            await db.rollback()
            msg = str(getattr(exc, "orig", exc))
            # Гонка за tasks.number — повторяем (до исчерпания попыток).
            if "tasks.number" in msg and attempt < attempts - 1:
                continue
            if "tasks.number" in msg:
                raise HTTPException(
                    status_code=503,
                    detail="Не удалось присвоить номер задаче, повторите попытку.",
                )
            # Иная ошибка целостности — честное сообщение вместо «номера».
            raise HTTPException(
                status_code=400,
                detail="Не удалось сохранить задачу: проверьте поля.",
            )
    # IncomeExpenseEntry linkage is created only when ALL required pieces
    # are present. Budget-only tasks (no category/payer/payee/due_date)
    # save without producing a treasury entry — we no longer error out.
    if (
        task.budget and task.budget > 0
        and task.category_code and task.payer_id and task.payee_id and task.due_date
    ):
        plan_date = _plan_date_from_due(task.due_date)
        if plan_date:
            entry = IncomeExpenseEntry(
                direction="expense",
                amount=abs(task.budget),
                plan_date=plan_date,
                payer_id=task.payer_id,
                payee_id=task.payee_id,
                deal_id=task.deal_id,
                category_code=task.category_code
            )
            db.add(entry)
            await db.commit()
            await db.refresh(entry)
            db_task = await Task.update(db, db_task.id, income_expense_id=str(entry.id))
    # Sync M2M assignee / watcher lists. Pick primary from explicit
    # assignee_ids when provided, else fall back to assigned_to_user_id.
    assignee_set = _resolve_assignee_set(task)
    if assignee_set is not None:
        await _sync_task_assignees(db, str(db_task.id), assignee_set)
        # Keep legacy `assigned_to_user_id` in sync with first item.
        primary = assignee_set[0] if assignee_set else None
        if str(db_task.assigned_to_user_id or '') != str(primary or ''):
            db_task = await Task.update(db, db_task.id, assigned_to_user_id=primary)
    if task.watcher_ids is not None:
        watchers_diff = await _sync_task_watchers(db, str(db_task.id), task.watcher_ids)
        if watchers_diff and (watchers_diff["added"] or watchers_diff["removed"]):
            await emit_event_safe(
                db,
                event_type="task.after_watchers_change",
                entity_type="task",
                entity_id=str(db_task.id),
                payload={
                    "task_id": str(db_task.id),
                    "added_user_ids": watchers_diff["added"],
                    "removed_user_ids": watchers_diff["removed"],
                    "final_user_ids": watchers_diff["final"],
                    "changed_by_user_id": str(user.id) if user else None,
                },
                payload_version=1,
            )

    if db_task.assigned_to_user_id and db_task.notify_assigned:
        try:
            await log_event(
                db,
                entity_type="task",
                entity_id=str(db_task.id),
                action="task.assign",
                created_by=str(user.id),
                details={
                    "task_id": str(db_task.id),
                    "task_title": db_task.title,
                    "deal_id": str(db_task.deal_id) if db_task.deal_id else None,
                    "assigned_to_user_id": str(db_task.assigned_to_user_id),
                },
            )
        except Exception:
            pass
    if db_task.deal_id:
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(db_task.deal_id),
                action="task.create",
                created_by=str(user.id),
                details={
                    "task_id": str(db_task.id),
                    "task_title": db_task.title,
                    "deal_id": str(db_task.deal_id),
                    "assigned_to_user_id": str(db_task.assigned_to_user_id) if db_task.assigned_to_user_id else None,
                },
            )
        except Exception:
            pass
    # Attach M2M lists onto the model instance so pydantic picks them up.
    people = await _load_task_people(db, str(db_task.id))
    db_task.assignee_ids = people["assignee_ids"]
    db_task.watcher_ids = people["watcher_ids"]
    # Event bus: внешние подписчики получают факт создания задачи.
    from app.services.event_outbox import emit_event_safe
    await emit_event_safe(
        db,
        event_type="task.after_create",
        entity_type="task",
        entity_id=str(db_task.id),
        payload={
            "id": str(db_task.id),
            "number": db_task.number,
            "title": db_task.title,
            "status": db_task.status,
            "priority": db_task.priority,
            "deal_id": str(db_task.deal_id) if db_task.deal_id else None,
            "assigned_to_user_id": str(db_task.assigned_to_user_id) if db_task.assigned_to_user_id else None,
            "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
            "due_time": db_task.due_time,
            "created_by_user_id": str(user.id) if user else None,
        },
    )
    await db.commit()
    return db_task


@router.put("/matrix/reorder")
async def reorder_task_matrix(
    payload: TaskMatrixReorder,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Сохранить персональный порядок задач внутри квадранта матрицы."""
    if payload.quadrant not in MATRIX_QUADRANTS:
        raise HTTPException(status_code=400, detail="Invalid matrix quadrant")

    task_ids = []
    seen = set()
    for raw_id in payload.task_ids:
        value = str(raw_id or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        task_ids.append(value)

    if not task_ids:
        return {"updated": 0}

    result = await db.execute(select(Task).where(Task.id.in_(task_ids)))
    tasks = {str(task.id): task for task in result.scalars().all()}

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
    if not read_all:
        if not read_assigned:
            return {"updated": 0}
        uid = str(user.id)
        # «Свои» = main assignee | postановщик | multi-assignee | watcher.
        ta_ids = set(map(str, (await db.execute(
            select(TaskAssignee.task_id)
            .where(TaskAssignee.user_id == uid)
            .where(TaskAssignee.task_id.in_(list(tasks.keys())))
        )).scalars().all()))
        tw_ids = set(map(str, (await db.execute(
            select(TaskWatcher.task_id)
            .where(TaskWatcher.user_id == uid)
            .where(TaskWatcher.task_id.in_(list(tasks.keys())))
        )).scalars().all()))
        tasks = {
            task_id: task
            for task_id, task in tasks.items()
            if str(task.assigned_to_user_id) == uid
               or str(task.created_by_user_id) == uid
               or task_id in ta_ids
               or task_id in tw_ids
        }

    if not tasks:
        return {"updated": 0}

    existing_result = await db.execute(
        select(TaskUserMatrix)
        .where(TaskUserMatrix.user_id == str(user.id))
        .where(TaskUserMatrix.task_id.in_(list(tasks.keys())))
    )
    existing = {str(item.task_id): item for item in existing_result.scalars().all()}

    updated = 0
    for index, task_id in enumerate(task_ids):
        if task_id not in tasks:
            continue
        position = existing.get(task_id)
        if position:
            position.quadrant = payload.quadrant
            position.sort_order = index
        else:
            db.add(TaskUserMatrix(
                task_id=task_id,
                user_id=str(user.id),
                quadrant=payload.quadrant,
                sort_order=index,
            ))
        updated += 1

    await db.commit()
    return {"updated": updated}


@router.put("/{task_id}/matrix")
async def update_task_matrix_position(
    task_id: str,
    payload: TaskMatrixUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обновить персональный квадрант задачи для текущего пользователя."""
    if payload.quadrant not in MATRIX_QUADRANTS:
        raise HTTPException(status_code=400, detail="Invalid matrix quadrant")

    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    result = await db.execute(
        select(TaskUserMatrix)
        .where(TaskUserMatrix.user_id == str(user.id))
        .where(TaskUserMatrix.task_id == str(task.id))
    )
    position = result.scalar_one_or_none()
    if position:
        position.quadrant = payload.quadrant
        position.sort_order = int(payload.sort_order or 0)
    else:
        position = TaskUserMatrix(
            task_id=str(task.id),
            user_id=str(user.id),
            quadrant=payload.quadrant,
            sort_order=int(payload.sort_order or 0),
        )
        db.add(position)
    await db.commit()
    await db.refresh(position)

    return {
        "task_id": str(task.id),
        "matrix_quadrant": position.quadrant,
        "matrix_sort_order": position.sort_order,
        "matrix_manual": True,
    }


@router.get("/{task_id}", response_model=TaskWithRelations)
async def get_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Получить задачу по ID"""
    from sqlalchemy.orm import joinedload
    task_uuid = _parse_uuid(task_id, "task_id")
    query = select(Task).options(
        joinedload(Task.deal),
        joinedload(Task.stage),
        joinedload(Task.assigned_to),
        joinedload(Task.created_by),
        joinedload(Task.assigned_to_user),
        joinedload(Task.created_by_user),
        joinedload(Task.payer),
        joinedload(Task.payee)
    ).where(Task.id == task_uuid)
    result = await db.execute(query)
    task = result.unique().scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Единая логика прав через helper — учитывает creator/multi-assignee/watcher.
    await _require_task_access(db, user, task)

    matrix_map = await _get_user_matrix_map(db, str(user.id), [str(task.id)])
    people = await _load_task_people(db, str(task.id))
    return _apply_matrix_fields({
        "id": str(task.id),
        "number": task.number,
        "title": task.title,
        "description": task.description,
        "deal_id": str(task.deal_id) if task.deal_id else None,
        "stage_id": str(task.stage_id) if task.stage_id else None,
        "status": task.status,
        "priority": task.priority,
        "work_category": task.work_category,
        "assigned_to_id": str(task.assigned_to_id) if task.assigned_to_id else None,
        "created_by_id": str(task.created_by_id) if task.created_by_id else None,
        "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
        "created_by_user_id": str(task.created_by_user_id) if task.created_by_user_id else None,
        "payer_id": str(task.payer_id) if task.payer_id else None,
        "payee_id": str(task.payee_id) if task.payee_id else None,
        "start_date": task.start_date,
        "due_date": task.due_date,
        "due_time": task.due_time,
        "completed_at": task.completed_at,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "tags": task.tags or [],
        "attachments": _sanitize_task_attachments(task.attachments or []),
        "notify_assigned": task.notify_assigned,
        "notify_overdue": task.notify_overdue,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "final_budget": task.final_budget,
        "rating_coefficient": task.rating_coefficient,
        "deadline_coefficient": task.deadline_coefficient,
        "penalty_amount": task.penalty_amount,
        "deal_title": task.deal.title if task.deal else None,
        "stage_name": task.stage.name if task.stage else None,
        "assigned_to_name": task.assigned_to.name if task.assigned_to else None,
        "created_by_name": task.created_by.name if task.created_by else None,
        "assigned_to_user_name": task.assigned_to_user.full_name if task.assigned_to_user else None,
        "assigned_to_user_avatar_url": task.assigned_to_user.avatar_url if task.assigned_to_user else None,
        "created_by_user_name": task.created_by_user.full_name if task.created_by_user else None,
        "created_by_user_avatar_url": task.created_by_user.avatar_url if task.created_by_user else None,
        "payer_name": task.payer.name if task.payer else None,
        "payee_name": task.payee.name if task.payee else None,
        "assignee_ids": people["assignee_ids"],
        "watcher_ids": people["watcher_ids"],
    }, task, matrix_map)


@router.post("/{task_id}/attachments")
async def upload_task_attachments(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Upload attachments for a task."""
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)
    form = await request.form()
    raw_files = form.getlist("files")
    files_list = [
        item
        for item in raw_files
        if getattr(item, "filename", None) and callable(getattr(item, "read", None))
    ]
    if not files_list:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    root = settings.STORAGE_LOCAL_ROOT or "/"
    base_path = f"{root.rstrip('/')}/_tasks/{task.id}/attachments"
    await ensure_path(base_path)

    max_bytes = int(settings.UPLOAD_TMP_MAX_BYTES or 256 * 1024 * 1024)
    attachments = _sanitize_task_attachments(task.attachments or [])
    for upload in files_list:
        if not upload or not upload.filename:
            continue
        temp_path = None
        try:
            temp_path, size_bytes = await write_upload_to_tmp(upload, max_bytes)
            safe_name = clean_name(upload.filename or "attachment")
            stored_name = f"{uuid.uuid4().hex}_{safe_name}"
            file_path = f"{base_path.rstrip('/')}/{stored_name}"
            await upload_file_with_safe_extension(file_path, temp_path)
            attachments.append(
                {
                    "name": safe_name,
                    "path": file_path,
                    "size": size_bytes,
                    "content_type": upload.content_type,
                }
            )
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    task = await Task.update(db, task.id, attachments=attachments)
    return {"attachments": _sanitize_task_attachments(task.attachments or [])}


@router.delete("/{task_id}/attachments")
async def delete_task_attachment(
    task_id: str,
    path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Delete a specific task attachment."""
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_access(db, user, task)

    attachments = _sanitize_task_attachments(task.attachments or [])
    match = next((item for item in attachments if str(item.get("path") or "") == str(path)), None)
    if not match:
        raise HTTPException(status_code=404, detail="Attachment not found")

    try:
        await delete_path(path, permanently=True)
    except Exception:
        pass

    updated_attachments = [item for item in attachments if str(item.get("path") or "") != str(path)]
    task = await Task.update(db, task.id, attachments=updated_attachments)
    return {"attachments": _sanitize_task_attachments(task.attachments or [])}

@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обновить задачу"""
    # Фильтруем None значения. Списки assignee_ids / watcher_ids вынимаем
    # отдельно — их пустой массив должен иметь смысл «очистить», а None
    # должен означать «не трогать», поэтому через `filtered_data` они не идут.
    incoming_assignee_ids = task_update.assignee_ids
    incoming_watcher_ids = task_update.watcher_ids
    filtered_data = {
        k: v for k, v in task_update.dict().items()
        if v is not None and k not in ("assignee_ids", "watcher_ids")
    }
    # Пустая строка в FK-поле -> NULL (иначе FOREIGN KEY constraint failed).
    _FK_BLANK = (
        "deal_id", "stage_id", "assigned_to_id", "created_by_id",
        "assigned_to_user_id", "created_by_user_id", "payer_id", "payee_id",
        "income_expense_id", "source_auction_id",
    )
    for _fk in _FK_BLANK:
        if _fk in filtered_data and isinstance(filtered_data[_fk], str) and not filtered_data[_fk].strip():
            filtered_data[_fk] = None
    if 'attachments' in filtered_data:
        filtered_data['attachments'] = _sanitize_task_attachments(filtered_data.get('attachments'))
    if not filtered_data and incoming_assignee_ids is None and incoming_watcher_ids is None:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    # If assignee_ids is provided, derive the legacy primary
    # `assigned_to_user_id` from it (first entry; null when empty).
    if incoming_assignee_ids is not None:
        primary = str(incoming_assignee_ids[0]) if incoming_assignee_ids else None
        filtered_data['assigned_to_user_id'] = primary
    if not filtered_data and (incoming_assignee_ids is not None or incoming_watcher_ids is not None):
        # Still need to fetch task for downstream logic; insert a no-op marker
        filtered_data = {}

    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await ensure_can_edit_record(db, request, user, "tasks", task)
    previous_assigned_user_id = str(task.assigned_to_user_id) if task.assigned_to_user_id else None
    # Снимок «до» — для event bus: смена статуса = отдельное событие,
    # смена дедлайна = отдельное событие (для синка с календарём).
    _prev_task_status = task.status
    _prev_task_due_date = task.due_date
    _prev_task_due_time = task.due_time

    # Проверяем существование связанных объектов
    if 'deal_id' in filtered_data and filtered_data['deal_id']:
        deal = await Deal.get_by_id(db, filtered_data['deal_id'])
        if not deal:
            raise HTTPException(status_code=404, detail="Проект не найден")
    if 'stage_id' in filtered_data and filtered_data['stage_id']:
        stage = await Stage.get_by_id(db, filtered_data['stage_id'])
        if not stage:
            raise HTTPException(status_code=404, detail="Этап не найден")

    if 'assigned_to_id' in filtered_data and filtered_data['assigned_to_id']:
        assigned_to = await Company.get_by_id(db, filtered_data['assigned_to_id'])
        if not assigned_to:
            raise HTTPException(status_code=404, detail="Ответственный не найден")
    if 'payer_id' in filtered_data and filtered_data['payer_id']:
        payer = await Company.get_by_id(db, filtered_data['payer_id'])
        if not payer:
            raise HTTPException(status_code=404, detail="Payer company not found")
    if 'payee_id' in filtered_data and filtered_data['payee_id']:
        payee = await Company.get_by_id(db, filtered_data['payee_id'])
        if not payee:
            raise HTTPException(status_code=404, detail="Payee company not found")

    # Если статус меняется на completed, устанавливаем completed_at
    if 'assigned_to_user_id' in filtered_data and filtered_data['assigned_to_user_id']:
        assigned_user = await User.get_by_id(db, filtered_data['assigned_to_user_id'])
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        filtered_data['assigned_to_user_id'] = str(assigned_user.id)
    if 'created_by_user_id' in filtered_data and filtered_data['created_by_user_id']:
        created_user = await User.get_by_id(db, filtered_data['created_by_user_id'])
        if not created_user:
            raise HTTPException(status_code=404, detail="Created user not found")
        filtered_data['created_by_user_id'] = str(created_user.id)
    if 'status' in filtered_data and filtered_data['status'] == 'completed':
        await ensure_entity_action_allowed(
            db,
            entity_type="task",
            entity_id=str(task.id),
            action_label="завершение задачи",
        )
        from datetime import datetime
        filtered_data['completed_at'] = datetime.now()

    new_status = filtered_data.get("status", task.status)
    new_budget = filtered_data.get("budget", task.budget)
    new_category = filtered_data.get("category_code", task.category_code)
    new_payer = filtered_data.get("payer_id", task.payer_id)
    new_payee = filtered_data.get("payee_id", task.payee_id)
    new_due_date = filtered_data.get("due_date", task.due_date)
    # Budget validation temporarily disabled — saving a task with budget
    # but without category/payer/payee/due_date is now allowed; we simply
    # skip the IncomeExpenseEntry sync further down in that case.

    # Convert UUID objects to strings for SQLite compatibility
    import uuid as uuid_module
    for key, value in filtered_data.items():
        if isinstance(value, (uuid.UUID, uuid_module.UUID)):
            filtered_data[key] = str(value)

    if filtered_data:
        task = await Task.update(db, task_id, **filtered_data)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
    # Sync M2M lists (assignee_ids / watcher_ids). `None` means no change.
    if incoming_assignee_ids is not None:
        await _sync_task_assignees(db, str(task.id), [str(x) for x in incoming_assignee_ids])
    if incoming_watcher_ids is not None:
        watchers_diff = await _sync_task_watchers(db, str(task.id), [str(x) for x in incoming_watcher_ids])
        if watchers_diff and (watchers_diff["added"] or watchers_diff["removed"]):
            await emit_event_safe(
                db,
                event_type="task.after_watchers_change",
                entity_type="task",
                entity_id=str(task.id),
                payload={
                    "task_id": str(task.id),
                    "added_user_ids": watchers_diff["added"],
                    "removed_user_ids": watchers_diff["removed"],
                    "final_user_ids": watchers_diff["final"],
                    "changed_by_user_id": str(user.id) if user else None,
                },
                payload_version=1,
            )
    full_budget_payload = (
        task.budget and task.budget > 0
        and task.category_code and task.payer_id and task.payee_id and task.due_date
    )
    if full_budget_payload:
        plan_date = _plan_date_from_due(task.due_date)
        if not plan_date:
            full_budget_payload = False
    if full_budget_payload:
        entry = None
        if task.income_expense_id:
            result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == task.income_expense_id))
            entry = result.scalar_one_or_none()
        if entry:
            entry.direction = "expense"
            entry.amount = abs(task.budget)
            entry.plan_date = plan_date
            entry.payer_id = task.payer_id
            entry.payee_id = task.payee_id
            entry.deal_id = task.deal_id
            entry.category_code = task.category_code
            await db.commit()
        else:
            entry = IncomeExpenseEntry(
                direction="expense",
                amount=abs(task.budget),
                plan_date=plan_date,
                payer_id=task.payer_id,
                payee_id=task.payee_id,
                deal_id=task.deal_id,
                category_code=task.category_code
            )
            db.add(entry)
            await db.commit()
            await db.refresh(entry)
            task = await Task.update(db, task.id, income_expense_id=str(entry.id))
    else:
        # Drop the IncomeExpense linkage only when the budget itself is cleared.
        # Don't delete it just because other required fields are missing —
        # the entry can be revisited later when category/payer/payee are filled.
        if task.income_expense_id and not (task.budget and task.budget > 0):
            await db.execute(delete(IncomeExpenseEntry).where(IncomeExpenseEntry.id == task.income_expense_id))
            await db.commit()
            task = await Task.update(db, task.id, income_expense_id=None)
    
    # Расчёт штрафов/бонусов только один раз после завершения и оценки
    if task.status == 'completed' and task.executor_rating and task.budget and task.budget > 0:
        should_compute = all(
            value is None for value in (
                task.final_budget,
                task.penalty_amount,
                task.rating_coefficient,
                task.deadline_coefficient
            )
        )
        if should_compute:
            rating_coef, deadline_coef, final_budget, penalty_amount = await calculate_penalty_coefficients(db, task)
            if rating_coef is not None:
                task = await Task.update(
                    db, task.id,
                    rating_coefficient=rating_coef,
                    deadline_coefficient=deadline_coef,
                    final_budget=final_budget,
                    penalty_amount=penalty_amount
                )
    new_assigned_user_id = str(task.assigned_to_user_id) if task.assigned_to_user_id else None
    # Нормализуем UUID — иначе строки с/без дефисов / разный case дадут
    # false-negative равенства, и пользователю прилетит уведомление
    # «назначена задача» при простой смене due_date (assignee тот же,
    # но строковые представления отличаются).
    def _norm_uuid(v):
        if not v:
            return None
        return str(v).strip().lower().replace('-', '')
    _prev_norm = _norm_uuid(previous_assigned_user_id)
    _new_norm = _norm_uuid(new_assigned_user_id)
    if _new_norm and _new_norm != _prev_norm and task.notify_assigned:
        try:
            await log_event(
                db,
                entity_type="task",
                entity_id=str(task.id),
                action="task.assign",
                created_by=str(user.id),
                details={
                    "task_id": str(task.id),
                    "task_title": task.title,
                    "deal_id": str(task.deal_id) if task.deal_id else None,
                    "assigned_to_user_id": new_assigned_user_id,
                },
            )
        except Exception:
            pass
        # Event Bus v2: after_assign — Telegram-бот подпишется и
        # пингует исполнителя, не дожидаясь поллинга уведомлений.
        from app.services.event_outbox import emit_event_safe as _emit_assign
        await _emit_assign(
            db,
            event_type="task.after_assign",
            entity_type="task",
            entity_id=str(task.id),
            payload={
                "id": str(task.id),
                "title": task.title,
                "deal_id": str(task.deal_id) if task.deal_id else None,
                "assigned_to_user_id": new_assigned_user_id,
                "previous_assigned_user_id": previous_assigned_user_id,
                "due_date": str(task.due_date) if task.due_date else None,
                "due_time": task.due_time,
                "priority": task.priority,
            },
        )
    if task.deal_id:
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(task.deal_id),
                action="task.update",
                created_by=str(user.id),
                details={
                    "task_id": str(task.id),
                    "task_title": task.title,
                    "deal_id": str(task.deal_id),
                    "assigned_to_user_id": new_assigned_user_id,
                },
            )
        except Exception:
            pass
    # Attach M2M lists onto the model so pydantic can serialize them.
    people = await _load_task_people(db, str(task.id))
    task.assignee_ids = people["assignee_ids"]
    task.watcher_ids = people["watcher_ids"]
    # Event bus: смена статуса — частое событие для интеграций
    # (Telegram-каналы исполнителей, BI-метрики throughput).
    if _prev_task_status and task.status and _prev_task_status != task.status:
        from app.services.event_outbox import emit_event_safe
        await emit_event_safe(
            db,
            event_type="task.after_status_change",
            entity_type="task",
            entity_id=str(task.id),
            payload={
                "id": str(task.id),
                "number": task.number,
                "title": task.title,
                "status_from": _prev_task_status,
                "status_to": task.status,
                "deal_id": str(task.deal_id) if task.deal_id else None,
                "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                "actor_user_id": str(user.id) if user else None,
            },
        )
        await db.commit()

    # Event Bus v2: смена дедлайна — отдельное событие для синка с
    # календарём (Google/Yandex/Outlook). Эмитим если due_date ИЛИ
    # due_time изменились. Сравниваем напрямую (date/str), не
    # парсим — роутер уже привёл к каноническим типам.
    if (_prev_task_due_date != task.due_date) or (_prev_task_due_time != task.due_time):
        from app.services.event_outbox import emit_event_safe
        await emit_event_safe(
            db,
            event_type="task.after_deadline_change",
            entity_type="task",
            entity_id=str(task.id),
            payload={
                "id": str(task.id),
                "title": task.title,
                "due_date_before": str(_prev_task_due_date) if _prev_task_due_date else None,
                "due_date_after": str(task.due_date) if task.due_date else None,
                "due_time_before": _prev_task_due_time,
                "due_time_after": task.due_time,
                "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                "deal_id": str(task.deal_id) if task.deal_id else None,
            },
        )
    return task


@router.post("/{task_id}/recalculate-penalty")
async def recalculate_task_penalty(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Принудительно пересчитать штраф/бонус по задаче"""
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if not task.budget or task.budget <= 0:
        raise HTTPException(status_code=400, detail="У задачи нет бюджета")
    if task.status != "completed" or not task.executor_rating:
        raise HTTPException(status_code=400, detail="Для пересчета нужна завершенная задача с оценкой")

    rating_coef, deadline_coef, final_budget, penalty_amount = await calculate_penalty_coefficients(db, task)
    if rating_coef is None:
        raise HTTPException(status_code=400, detail="Нет данных для пересчета")

    task = await Task.update(
        db, task.id,
        rating_coefficient=rating_coef,
        deadline_coefficient=deadline_coef,
        final_budget=final_budget,
        penalty_amount=penalty_amount
    )

    return {
        "message": "Пересчитано",
        "task_id": str(task.id),
        "final_budget": task.final_budget,
        "rating_coefficient": task.rating_coefficient,
        "deadline_coefficient": task.deadline_coefficient,
        "penalty_amount": task.penalty_amount
    }

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить задачу"""
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await ensure_can_edit_record(db, request, user, "tasks", task)
    # Чистим зависимые таблицы которые НЕ имеют FK ON DELETE CASCADE:
    # task_messages, task_reads, task_subtasks (NO ACTION). Без этого
    # DELETE FROM tasks падает с FOREIGN KEY constraint failed.
    # CASCADE-таблицы (task_assignees, task_watchers, task_user_matrix,
    # legal_case_tasks) удалятся автоматически, но для надёжности гасим
    # task_user_matrix явно (был тут до фикса). Для внешних ссылок
    # support_tickets.linked_task_id и task_auctions.created_task_id —
    # SET NULL чтобы не терять сами тикеты/аукционы.
    tid = str(task_id)
    await db.execute(text("DELETE FROM task_messages WHERE task_id = :tid"), {"tid": tid})
    await db.execute(text("DELETE FROM task_reads WHERE task_id = :tid"), {"tid": tid})
    await db.execute(text("DELETE FROM task_subtasks WHERE task_id = :tid"), {"tid": tid})
    await db.execute(text("UPDATE support_tickets SET linked_task_id = NULL WHERE linked_task_id = :tid"), {"tid": tid})
    await db.execute(text("UPDATE task_auctions SET created_task_id = NULL WHERE created_task_id = :tid"), {"tid": tid})
    await db.execute(delete(TaskUserMatrix).where(TaskUserMatrix.task_id == tid))
    await db.commit()
    success = await Task.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Event Bus v2: after_delete для синхронизации внешних систем.
    from app.services.event_outbox import emit_event_safe
    await emit_event_safe(
        db,
        event_type="task.after_delete",
        entity_type="task",
        entity_id=str(task.id),
        payload={
            "id": str(task.id),
            "title": task.title,
            "deal_id": str(task.deal_id) if task.deal_id else None,
        },
    )
    return {"message": "Задача удалена"}

@router.get("/deals/{deal_id}/tasks", response_model=List[TaskWithRelations])
async def get_deal_tasks(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить все задачи проекта"""
    # Проверяем существование проекта
    deal = await Deal.get_by_id(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")

    from sqlalchemy.orm import joinedload
    query = select(Task).options(
        joinedload(Task.deal),
        joinedload(Task.stage),
        joinedload(Task.assigned_to),
        joinedload(Task.created_by),
        joinedload(Task.assigned_to_user),
        joinedload(Task.created_by_user),
        joinedload(Task.payer),
        joinedload(Task.payee)
    ).where(Task.deal_id == deal_id).order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.unique().scalars().all()
    people_map = await _load_task_people_batch(db, [str(t.id) for t in tasks])

    response_tasks = []
    for task in tasks:
        people = people_map.get(str(task.id), {"assignee_ids": [], "watcher_ids": []})
        response_tasks.append({
            "id": str(task.id),
            "number": task.number,
            "title": task.title,
            "description": task.description,
            "deal_id": str(task.deal_id),
            "stage_id": str(task.stage_id) if task.stage_id else None,
            "status": task.status,
            "priority": task.priority,
            "work_category": task.work_category,
            "assigned_to_id": str(task.assigned_to_id) if task.assigned_to_id else None,
            "created_by_id": str(task.created_by_id) if task.created_by_id else None,
            "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
            "created_by_user_id": str(task.created_by_user_id) if task.created_by_user_id else None,
            "payer_id": str(task.payer_id) if task.payer_id else None,
            "payee_id": str(task.payee_id) if task.payee_id else None,
            "start_date": task.start_date,
            "due_date": task.due_date,
            "due_time": task.due_time,
            "completed_at": task.completed_at,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "tags": task.tags or [],
            "attachments": _sanitize_task_attachments(task.attachments or []),
            "notify_assigned": task.notify_assigned,
            "notify_overdue": task.notify_overdue,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "final_budget": task.final_budget,
            "rating_coefficient": task.rating_coefficient,
            "deadline_coefficient": task.deadline_coefficient,
            "penalty_amount": task.penalty_amount,
            "deal_title": task.deal.title if task.deal else None,
            "stage_name": task.stage.name if task.stage else None,
            "assigned_to_name": task.assigned_to.name if task.assigned_to else None,
            "created_by_name": task.created_by.name if task.created_by else None,
            "assigned_to_user_name": task.assigned_to_user.full_name if task.assigned_to_user else None,
            "assigned_to_user_avatar_url": task.assigned_to_user.avatar_url if task.assigned_to_user else None,
            "created_by_user_name": task.created_by_user.full_name if task.created_by_user else None,
            "created_by_user_avatar_url": task.created_by_user.avatar_url if task.created_by_user else None,
            "payer_name": task.payer.name if task.payer else None,
            "payee_name": task.payee.name if task.payee else None,
            "assignee_ids": people["assignee_ids"],
            "watcher_ids": people["watcher_ids"],
        })

    return response_tasks
