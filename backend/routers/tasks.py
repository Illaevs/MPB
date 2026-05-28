"""
Tasks API Router
"""
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Body, Request, File, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.database.session import get_db
from app.models import Task, TaskUserMatrix, Deal, Stage, Company, User, IncomeExpenseEntry, PenaltyRule
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskWithRelations
from app.core.auth_middleware import CurrentUser
from app.services.event_log import log_event
from app.services.approval_runtime import ensure_entity_action_allowed
from app.services.permissions import get_section_permissions
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
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
    if read_all:
        return
    if not read_assigned or str(task.assigned_to_user_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Задача не найдена")


def _serialize_task(task: Task) -> Dict[str, Any]:
    return {
        "id": str(task.id) if task.id else None,
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
    skip: int = 0,
    limit: int = 100,
    deal_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    status: Optional[str] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Получить список всех задач с фильтрами"""
    try:
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
        )

        deal_uuid = _parse_uuid(deal_id, "deal_id") if deal_id else None
        assigned_uuid = _parse_uuid(assigned_to_id, "assigned_to_id") if assigned_to_id else None
        if deal_uuid:
            query = query.where(Task.deal_id == deal_uuid)
        if assigned_uuid:
            query = query.where(Task.assigned_to_id == assigned_uuid)
        if assigned_to_user_id:
            assigned_user_uuid = _parse_uuid(assigned_to_user_id, "assigned_to_user_id")
            query = query.where(Task.assigned_to_user_id == assigned_user_uuid)
        if status:
            query = query.where(Task.status == status)

        # Фильтрация по диапазону дат дедлайна
        if due_date_from:
            parsed_from = _to_date(due_date_from)
            if parsed_from:
                query = query.where(Task.due_date >= parsed_from)
        if due_date_to:
            parsed_to = _to_date(due_date_to)
            if parsed_to:
                query = query.where(Task.due_date <= parsed_to)

        read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
        if not read_all:
            if not read_assigned:
                return []
            query = query.where(Task.assigned_to_user_id == str(user.id))

        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        result = await db.execute(query)
        tasks = result.unique().scalars().all()
        matrix_map = await _get_user_matrix_map(db, str(user.id), [str(task.id) for task in tasks])

        # Формируем ответ с названиями
        response_tasks = []
        for task in tasks:
            task_dict = {
                "id": str(task.id) if task.id else None,
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
    if task.budget and task.budget > 0:
        if not task.category_code or not task.payer_id or not task.payee_id or not task.due_date:
            raise HTTPException(status_code=400, detail="category_code, payer_id, payee_id and due_date required for task with budget")
        payer = await Company.get_by_id(db, task.payer_id)
        if not payer:
            raise HTTPException(status_code=404, detail="Payer company not found")
        payee = await Company.get_by_id(db, task.payee_id)
        if not payee:
            raise HTTPException(status_code=404, detail="Payee company not found")

    # Create task with explicit parameters
    db_task = await Task.create(
        db,
        title=task.title,
        description=task.description,
        deal_id=task.deal_id,
        stage_id=task.stage_id if task.stage_id else None,
        status=task.status,
        priority=task.priority,
        assigned_to_id=task.assigned_to_id if task.assigned_to_id else None,
        created_by_id=task.created_by_id if task.created_by_id else None,
        assigned_to_user_id=str(assigned_user.id) if assigned_user else None,
        created_by_user_id=str(created_user.id) if created_user else None,
        start_date=task.start_date,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        budget=task.budget,
        category_code=task.category_code,
        work_category=task.work_category,
        payer_id=task.payer_id,
        payee_id=task.payee_id,
        tags=task.tags or [],
        attachments=_sanitize_task_attachments(task.attachments or []),
        notify_assigned=task.notify_assigned,
        notify_overdue=task.notify_overdue
    )
    if task.budget and task.budget > 0:
        plan_date = _plan_date_from_due(task.due_date)
        if not plan_date:
            raise HTTPException(status_code=400, detail="Invalid due_date")
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
        tasks = {
            task_id: task
            for task_id, task in tasks.items()
            if str(task.assigned_to_user_id) == str(user.id)
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

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "tasks")
    if not read_all:
        if not read_assigned or str(task.assigned_to_user_id) != str(user.id):
            raise HTTPException(status_code=404, detail="Р—Р°РґР°С‡Р° РЅРµ РЅР°Р№РґРµРЅР°")

    matrix_map = await _get_user_matrix_map(db, str(user.id), [str(task.id)])
    return _apply_matrix_fields({
        "id": str(task.id),
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обновить задачу"""
    # Фильтруем None значения
    filtered_data = {k: v for k, v in task_update.dict().items() if v is not None}
    if 'attachments' in filtered_data:
        filtered_data['attachments'] = _sanitize_task_attachments(filtered_data.get('attachments'))
    if not filtered_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    previous_assigned_user_id = str(task.assigned_to_user_id) if task.assigned_to_user_id else None

    # Проверяем существование связанных объектов
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
    if new_budget and new_budget > 0:
        if not (new_category and str(new_category).strip() and new_payer and new_payee and new_due_date):
            raise HTTPException(status_code=400, detail="category_code, payer_id, payee_id and due_date required for task with budget")

    # Convert UUID objects to strings for SQLite compatibility
    import uuid as uuid_module
    for key, value in filtered_data.items():
        if isinstance(value, (uuid.UUID, uuid_module.UUID)):
            filtered_data[key] = str(value)

    task = await Task.update(db, task_id, **filtered_data)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.budget and task.budget > 0:
        plan_date = _plan_date_from_due(task.due_date)
        if not plan_date:
            raise HTTPException(status_code=400, detail="Invalid due_date")
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
        if task.income_expense_id:
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
    if new_assigned_user_id and new_assigned_user_id != previous_assigned_user_id and task.notify_assigned:
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
    db: AsyncSession = Depends(get_db)
):
    """Удалить задачу"""
    await db.execute(delete(TaskUserMatrix).where(TaskUserMatrix.task_id == str(task_id)))
    await db.commit()
    success = await Task.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена")
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

    response_tasks = []
    for task in tasks:
        response_tasks.append({
            "id": str(task.id),
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
        })

    return response_tasks
