"""
Approval workflows API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Notification, Role, User
from app.models.task import Task
from app.models.approval import (
    ApprovalActionLog,
    ApprovalInstance,
    ApprovalInstanceStep,
    ApprovalTemplate,
    ApprovalTemplateStep,
)
from app.schemas.approval import (
    ApprovalActionLogResponse,
    ApprovalInboxItem,
    ApprovalInboxResponse,
    ApprovalInboxStats,
    ApprovalInstanceAction,
    ApprovalInstanceResponse,
    ApprovalInstanceStart,
    ApprovalInstanceStepResponse,
    ApprovalTemplateResponse,
    ApprovalTemplateStepResponse,
    ApprovalTemplateWrite,
)
from app.services.permissions import (
    AUTHENTICATED_SECTION_KEYS,
    is_superuser,
    require_any_section_access,
    require_section_read,
    require_section_write,
)


router = APIRouter()

ENTITY_TYPE_OPTIONS = [
    {"value": "outgoing_document", "label": "Исходящий документ"},
    {"value": "contract", "label": "Договор"},
    {"value": "deal", "label": "Сделка"},
    {"value": "task", "label": "Задача"},
    {"value": "income_expense_entry", "label": "Запись ДДС"},
    {"value": "treasury_transaction", "label": "Операция казначейства"},
]
ALLOWED_ENTITY_TYPES = {item["value"] for item in ENTITY_TYPE_OPTIONS}
ALLOWED_ASSIGNEE_TYPES = {"user", "role"}
INSTANCE_ACTIVE_STATUSES = {"pending"}


def _normalize_text(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    return text or None


def _build_action_url(instance: ApprovalInstance) -> Optional[str]:
    if instance.entity_type == "outgoing_document":
        return f"/outgoing-registry?document_id={instance.entity_id}&approvalInstance={instance.id}"
    if instance.entity_type == "contract":
        return f"/contracts/{instance.entity_id}?approvalInstance={instance.id}"
    if instance.entity_type == "deal":
        return f"/projects/{instance.entity_id}?approvalInstance={instance.id}"
    if instance.entity_type == "task":
        return f"/tasks?task_id={instance.entity_id}&approvalInstance={instance.id}"
    return None


def _entity_type_label(entity_type: str) -> str:
    for item in ENTITY_TYPE_OPTIONS:
        if item["value"] == entity_type:
            return item["label"]
    return entity_type


async def _apply_entity_final_effect(db: AsyncSession, instance: ApprovalInstance) -> None:
    if instance.entity_type != "task":
        return
    task = await Task.get_by_id(db, str(instance.entity_id))
    if not task:
        return
    if task.status != "completed":
        task.status = "completed"
    if not task.completed_at:
        task.completed_at = datetime.utcnow()


def _step_targets_user(step: ApprovalInstanceStep, user: User) -> bool:
    if step.assignee_type == "user":
        return bool(step.assignee_user_id and str(step.assignee_user_id) == str(user.id))
    if step.assignee_type == "role":
        return bool(step.assignee_role_id and str(step.assignee_role_id) == str(user.role_id))
    return False


def _build_inbox_item(
    instance: ApprovalInstance,
    steps: Sequence[ApprovalInstanceStep],
    users: Dict[str, User],
    roles: Dict[str, Role],
    user: User,
) -> ApprovalInboxItem:
    ordered_steps = sorted(steps, key=lambda item: (int(item.step_order or 1), item.created_at or datetime.utcnow()))
    pending_step = next((item for item in ordered_steps if item.status == "pending"), None)
    rejected_step = next((item for item in ordered_steps if item.status == "rejected"), None)
    current_step = pending_step or rejected_step or (ordered_steps[-1] if ordered_steps else None)
    total_steps = len(ordered_steps)
    completed_steps = sum(1 for item in ordered_steps if item.status == "approved")
    current_step_order = int(current_step.step_order) if current_step else (total_steps or None)
    current_step_assignee_label = _assignee_label(current_step, users, roles) if current_step else None
    waiting_for_me = bool(pending_step and _step_targets_user(pending_step, user))
    involved_by_me = (
        str(instance.started_by or "") == str(user.id)
        or str(instance.completed_by or "") == str(user.id)
        or any(_step_targets_user(item, user) for item in ordered_steps)
        or any(str(item.acted_by or "") == str(user.id) for item in ordered_steps)
    )

    if instance.status == "approved":
        current_stage_label = "Завершено"
        progress_label = f"{total_steps}/{total_steps}" if total_steps else "0/0"
    elif instance.status == "rejected":
        current_stage_label = "Отклонено"
        progress_label = f"{current_step_order or completed_steps}/{total_steps}" if total_steps else "0/0"
    else:
        current_stage_label = current_step_assignee_label or "Ожидает согласования"
        progress_label = f"{current_step_order or (completed_steps + 1)}/{total_steps}" if total_steps else "0/0"

    started_user = users.get(str(instance.started_by)) if instance.started_by else None
    completed_user = users.get(str(instance.completed_by)) if instance.completed_by else None

    return ApprovalInboxItem(
        id=str(instance.id),
        template_name=instance.template_name,
        entity_type=instance.entity_type,
        entity_type_label=_entity_type_label(instance.entity_type),
        entity_id=str(instance.entity_id),
        entity_label=instance.entity_label,
        status=instance.status,
        started_by=str(instance.started_by) if instance.started_by else None,
        started_by_label=started_user.full_name if started_user else None,
        started_by_avatar_url=started_user.avatar_url if started_user else None,
        completed_by_label=completed_user.full_name if completed_user else None,
        completed_by_avatar_url=completed_user.avatar_url if completed_user else None,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
        total_steps=total_steps,
        completed_steps=completed_steps,
        current_step_order=current_step_order,
        current_step_title=current_step.title if current_step else None,
        current_step_assignee_label=current_step_assignee_label,
        progress_label=progress_label,
        current_stage_label=current_stage_label,
        waiting_for_me=waiting_for_me,
        involved_by_me=involved_by_me,
        action_url=_build_action_url(instance),
    )


async def _user_map(db: AsyncSession) -> Dict[str, User]:
    result = await db.execute(select(User).order_by(User.full_name))
    return {str(item.id): item for item in result.scalars().all()}


async def _role_map(db: AsyncSession) -> Dict[str, Role]:
    result = await db.execute(select(Role).order_by(Role.name))
    return {str(item.id): item for item in result.scalars().all()}


def _assignee_label(step, users: Dict[str, User], roles: Dict[str, Role]) -> Optional[str]:
    if step.assignee_type == "user" and step.assignee_user_id:
        user = users.get(str(step.assignee_user_id))
        return user.full_name if user else str(step.assignee_user_id)
    if step.assignee_type == "role" and step.assignee_role_id:
        role = roles.get(str(step.assignee_role_id))
        return role.name if role else str(step.assignee_role_id)
    return None


async def _instance_counts_for_templates(db: AsyncSession, template_ids: List[str]) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {tid: {"active": 0, "total": 0} for tid in template_ids}
    if not template_ids:
        return counts
    result = await db.execute(
        select(ApprovalInstance.template_id, ApprovalInstance.status)
        .where(ApprovalInstance.template_id.in_(template_ids))
    )
    for tid, status in result.all():
        key = str(tid)
        bucket = counts.setdefault(key, {"active": 0, "total": 0})
        bucket["total"] += 1
        if status == "pending":
            bucket["active"] += 1
    return counts


async def _serialize_template(
    db: AsyncSession,
    template: ApprovalTemplate,
    users: Optional[Dict[str, User]] = None,
    roles: Optional[Dict[str, Role]] = None,
    instance_counts: Optional[Dict[str, Dict[str, int]]] = None,
) -> ApprovalTemplateResponse:
    users = users or await _user_map(db)
    roles = roles or await _role_map(db)
    result = await db.execute(
        select(ApprovalTemplateStep)
        .where(ApprovalTemplateStep.template_id == str(template.id))
        .order_by(ApprovalTemplateStep.step_order, ApprovalTemplateStep.created_at)
    )
    steps = []
    for item in result.scalars().all():
        steps.append(
            ApprovalTemplateStepResponse(
                id=str(item.id),
                parent_step_id=str(item.parent_step_id) if item.parent_step_id else None,
                title=item.title,
                description=item.description,
                assignee_type=item.assignee_type,
                assignee_user_id=str(item.assignee_user_id) if item.assignee_user_id else None,
                assignee_role_id=str(item.assignee_role_id) if item.assignee_role_id else None,
                assignee_label=_assignee_label(item, users, roles),
                is_required=bool(item.is_required),
                step_order=int(item.step_order or 1),
            )
        )

    if instance_counts is None:
        instance_counts = await _instance_counts_for_templates(db, [str(template.id)])
    counts = instance_counts.get(str(template.id)) or {"active": 0, "total": 0}

    return ApprovalTemplateResponse(
        id=str(template.id),
        name=template.name,
        code=template.code,
        description=template.description,
        entity_type=template.entity_type,
        is_active=bool(template.is_active),
        tags=list(template.tags or []),
        created_by=str(template.created_by) if template.created_by else None,
        updated_by=str(template.updated_by) if template.updated_by else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
        steps=steps,
        active_instances_count=counts["active"],
        total_instances_count=counts["total"],
    )


async def _serialize_instance(
    db: AsyncSession,
    instance: ApprovalInstance,
    users: Optional[Dict[str, User]] = None,
    roles: Optional[Dict[str, Role]] = None,
) -> ApprovalInstanceResponse:
    users = users or await _user_map(db)
    roles = roles or await _role_map(db)

    steps_result = await db.execute(
        select(ApprovalInstanceStep)
        .where(ApprovalInstanceStep.instance_id == str(instance.id))
        .order_by(ApprovalInstanceStep.step_order, ApprovalInstanceStep.created_at)
    )
    action_result = await db.execute(
        select(ApprovalActionLog)
        .where(ApprovalActionLog.instance_id == str(instance.id))
        .order_by(ApprovalActionLog.created_at)
    )
    steps = [
        ApprovalInstanceStepResponse(
            id=str(item.id),
            template_step_id=str(item.template_step_id) if item.template_step_id else None,
            parent_template_step_id=str(item.parent_template_step_id) if item.parent_template_step_id else None,
            title=item.title,
            description=item.description,
            assignee_type=item.assignee_type,
            assignee_user_id=str(item.assignee_user_id) if item.assignee_user_id else None,
            assignee_role_id=str(item.assignee_role_id) if item.assignee_role_id else None,
            assignee_label=_assignee_label(item, users, roles),
            status=item.status,
            is_required=bool(item.is_required),
            step_order=int(item.step_order or 1),
            depth=int(item.depth or 0),
            acted_by=str(item.acted_by) if item.acted_by else None,
            acted_by_label=users.get(str(item.acted_by)).full_name if item.acted_by and users.get(str(item.acted_by)) else None,
            acted_at=item.acted_at,
            comment=item.comment,
        )
        for item in steps_result.scalars().all()
    ]
    actions = [
        ApprovalActionLogResponse(
            id=str(item.id),
            instance_step_id=str(item.instance_step_id) if item.instance_step_id else None,
            action=item.action,
            actor_user_id=str(item.actor_user_id) if item.actor_user_id else None,
            actor_label=users.get(str(item.actor_user_id)).full_name if item.actor_user_id and users.get(str(item.actor_user_id)) else None,
            comment=item.comment,
            payload_json=item.payload_json,
            created_at=item.created_at,
        )
        for item in action_result.scalars().all()
    ]
    started_user = users.get(str(instance.started_by)) if instance.started_by else None
    completed_user = users.get(str(instance.completed_by)) if instance.completed_by else None
    return ApprovalInstanceResponse(
        id=str(instance.id),
        template_id=str(instance.template_id),
        template_name=instance.template_name,
        entity_type=instance.entity_type,
        entity_id=str(instance.entity_id),
        entity_label=instance.entity_label,
        status=instance.status,
        current_step_id=str(instance.current_step_id) if instance.current_step_id else None,
        started_by=str(instance.started_by) if instance.started_by else None,
        started_by_label=started_user.full_name if started_user else None,
        completed_by=str(instance.completed_by) if instance.completed_by else None,
        completed_by_label=completed_user.full_name if completed_user else None,
        completed_comment=instance.completed_comment,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
        steps=steps,
        actions=actions,
    )


def _order_template_steps(steps: Sequence[ApprovalTemplateStep]) -> List[Tuple[ApprovalTemplateStep, int]]:
    by_parent: Dict[Optional[str], List[ApprovalTemplateStep]] = {}
    for item in steps:
        key = str(item.parent_step_id) if item.parent_step_id else None
        by_parent.setdefault(key, []).append(item)
    for items in by_parent.values():
        items.sort(key=lambda step: (int(step.step_order or 1), step.created_at or datetime.utcnow(), str(step.id)))

    ordered: List[Tuple[ApprovalTemplateStep, int]] = []

    def walk(parent_id: Optional[str], depth: int) -> None:
        for item in by_parent.get(parent_id, []):
            ordered.append((item, depth))
            walk(str(item.id), depth + 1)

    walk(None, 0)
    return ordered


async def _notify_for_step(db: AsyncSession, instance: ApprovalInstance, step: ApprovalInstanceStep) -> None:
    target_user_ids: List[str] = []
    if step.assignee_type == "user" and step.assignee_user_id:
        target_user_ids = [str(step.assignee_user_id)]
    elif step.assignee_type == "role" and step.assignee_role_id:
        result = await db.execute(
            select(User.id).where(User.role_id == str(step.assignee_role_id), User.is_active.is_(True))
        )
        target_user_ids = [str(item) for item in result.scalars().all()]

    action_url = _build_action_url(instance)

    for user_id in dict.fromkeys(target_user_ids):
        db.add(
            Notification(
                user_id=user_id,
                type="warning",
                priority="warning",
                title=f"Согласование: {instance.template_name}",
                message=f"Шаг «{step.title}» ожидает вашего решения.",
                entity_type="approval_instance",
                entity_id=str(instance.id),
                action_url=action_url,
            )
        )


async def _ensure_can_act(step: ApprovalInstanceStep, user: User) -> None:
    if step.assignee_type == "user":
        if not step.assignee_user_id or str(step.assignee_user_id) != str(user.id):
            raise HTTPException(status_code=403, detail="Этот шаг согласования назначен другому пользователю.")
        return
    if step.assignee_type == "role":
        if not step.assignee_role_id or str(step.assignee_role_id) != str(user.role_id):
            raise HTTPException(status_code=403, detail="Этот шаг согласования назначен другой роли.")
        return
    raise HTTPException(status_code=400, detail="Неизвестный тип исполнителя шага согласования.")


async def _user_involved_in_instance(
    db: AsyncSession, instance: ApprovalInstance, user: User
) -> bool:
    """M3: a user may see an approval instance only if they started it,
    completed it, or are/were a step assignee (by user or role) or actor."""
    uid = str(user.id)
    rid = str(user.role_id) if user.role_id else None
    if str(instance.started_by or "") == uid or str(instance.completed_by or "") == uid:
        return True
    result = await db.execute(
        select(ApprovalInstanceStep).where(
            ApprovalInstanceStep.instance_id == str(instance.id)
        )
    )
    for step in result.scalars().all():
        if step.assignee_type == "user" and str(step.assignee_user_id or "") == uid:
            return True
        if step.assignee_type == "role" and rid and str(step.assignee_role_id or "") == rid:
            return True
        if str(step.acted_by or "") == uid:
            return True
    return False


async def _template_steps_for_save(
    db: AsyncSession,
    template: ApprovalTemplate,
    payload_steps,
) -> None:
    client_id_to_db_id: Dict[str, str] = {}
    ordered_steps = sorted(payload_steps, key=lambda item: (int(item.step_order or 1), item.title.lower()))

    existing_result = await db.execute(
        select(ApprovalTemplateStep).where(ApprovalTemplateStep.template_id == str(template.id))
    )
    for item in existing_result.scalars().all():
        await db.delete(item)
    await db.flush()

    created_steps: List[Tuple[str, ApprovalTemplateStep]] = []
    for raw_step in ordered_steps:
        if raw_step.assignee_type not in ALLOWED_ASSIGNEE_TYPES:
            raise HTTPException(status_code=400, detail=f"Недопустимый тип исполнителя: {raw_step.assignee_type}")
        if raw_step.assignee_type == "user" and not raw_step.assignee_user_id:
            raise HTTPException(status_code=400, detail=f"Шаг «{raw_step.title}» должен иметь назначенного пользователя.")
        if raw_step.assignee_type == "role" and not raw_step.assignee_role_id:
            raise HTTPException(status_code=400, detail=f"Шаг «{raw_step.title}» должен иметь назначенную роль.")

        step = ApprovalTemplateStep(
            template_id=str(template.id),
            step_order=int(raw_step.step_order or 1),
            title=raw_step.title.strip(),
            description=_normalize_text(raw_step.description),
            assignee_type=raw_step.assignee_type,
            assignee_user_id=_normalize_text(raw_step.assignee_user_id),
            assignee_role_id=_normalize_text(raw_step.assignee_role_id),
            is_required=bool(raw_step.is_required),
        )
        db.add(step)
        await db.flush()
        created_steps.append((raw_step.client_id or str(step.id), step))
        client_id_to_db_id[raw_step.client_id or str(step.id)] = str(step.id)

    for raw_step in ordered_steps:
        parent_key = _normalize_text(raw_step.parent_client_id)
        if not parent_key:
            continue
        step_id = client_id_to_db_id.get(raw_step.client_id or "")
        parent_id = client_id_to_db_id.get(parent_key)
        if not step_id or not parent_id:
            raise HTTPException(status_code=400, detail=f"Не удалось связать дочерний шаг «{raw_step.title}».")
        result = await db.execute(select(ApprovalTemplateStep).where(ApprovalTemplateStep.id == step_id))
        step = result.scalar_one()
        step.parent_step_id = parent_id


@router.get("/meta")
async def get_approval_meta(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    users = await User.get_all(db)
    roles = await Role.get_all(db)
    return {
        "entity_types": ENTITY_TYPE_OPTIONS,
        "assignee_types": [
            {"value": "user", "label": "Пользователь"},
            {"value": "role", "label": "Роль"},
        ],
        "users": [
            {"id": str(item.id), "label": item.full_name, "email": item.email}
            for item in users
            if item.is_active
        ],
        "roles": [
            {"id": str(item.id), "label": item.name}
            for item in roles
        ],
        "instance_statuses": ["pending", "approved", "rejected", "cancelled"],
    }


@router.get("/templates", response_model=List[ApprovalTemplateResponse])
async def list_templates(
    entity_type: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    query = select(ApprovalTemplate).order_by(ApprovalTemplate.updated_at.desc(), ApprovalTemplate.created_at.desc())
    if entity_type:
        query = query.where(ApprovalTemplate.entity_type == entity_type)
    if active is not None:
        query = query.where(ApprovalTemplate.is_active == active)
    result = await db.execute(query)
    items = result.scalars().all()
    users = await _user_map(db)
    roles = await _role_map(db)
    counts = await _instance_counts_for_templates(db, [str(item.id) for item in items])
    return [await _serialize_template(db, item, users, roles, counts) for item in items]


@router.get("/templates/runtime", response_model=List[ApprovalTemplateResponse])
async def list_runtime_templates(
    entity_type: Optional[str] = Query(None),
    active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    query = select(ApprovalTemplate).order_by(ApprovalTemplate.updated_at.desc(), ApprovalTemplate.created_at.desc())
    if entity_type:
        query = query.where(ApprovalTemplate.entity_type == entity_type)
    if active is not None:
        query = query.where(ApprovalTemplate.is_active == active)
    result = await db.execute(query)
    users = await _user_map(db)
    roles = await _role_map(db)
    return [await _serialize_template(db, item, users, roles) for item in result.scalars().all()]


@router.get("/templates/{template_id}", response_model=ApprovalTemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    template = await db.get(ApprovalTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    return await _serialize_template(db, template)


@router.post("/templates", response_model=ApprovalTemplateResponse)
async def create_template(
    payload: ApprovalTemplateWrite,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("roles")),
):
    if payload.entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип сущности для шаблона согласования.")
    template = ApprovalTemplate(
        name=payload.name.strip(),
        code=_normalize_text(payload.code),
        description=_normalize_text(payload.description),
        entity_type=payload.entity_type,
        is_active=bool(payload.is_active),
        tags=[t.strip() for t in (payload.tags or []) if t and t.strip()],
        created_by=str(user.id),
        updated_by=str(user.id),
    )
    db.add(template)
    await db.flush()
    await _template_steps_for_save(db, template, payload.steps)
    await db.commit()
    await db.refresh(template)
    return await _serialize_template(db, template)


@router.put("/templates/{template_id}", response_model=ApprovalTemplateResponse)
async def update_template(
    template_id: str,
    payload: ApprovalTemplateWrite,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("roles")),
):
    template = await db.get(ApprovalTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    if payload.entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип сущности для шаблона согласования.")
    template.name = payload.name.strip()
    template.code = _normalize_text(payload.code)
    template.description = _normalize_text(payload.description)
    template.entity_type = payload.entity_type
    template.is_active = bool(payload.is_active)
    template.tags = [t.strip() for t in (payload.tags or []) if t and t.strip()]
    template.updated_by = str(user.id)
    await _template_steps_for_save(db, template, payload.steps)
    await db.commit()
    await db.refresh(template)
    return await _serialize_template(db, template)


@router.post("/templates/{template_id}/duplicate", response_model=ApprovalTemplateResponse)
async def duplicate_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("roles")),
):
    src = await db.get(ApprovalTemplate, str(template_id))
    if not src:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    steps_result = await db.execute(
        select(ApprovalTemplateStep).where(ApprovalTemplateStep.template_id == str(src.id))
    )
    src_steps = steps_result.scalars().all()

    clone = ApprovalTemplate(
        name=f"{src.name} (копия)",
        code=None,
        description=src.description,
        entity_type=src.entity_type,
        is_active=False,
        tags=list(src.tags or []),
        created_by=str(user.id),
        updated_by=str(user.id),
    )
    db.add(clone)
    await db.flush()

    id_map: Dict[str, str] = {}
    for s in src_steps:
        new_id = str(uuid.uuid4())
        id_map[str(s.id)] = new_id
    for s in src_steps:
        new_step = ApprovalTemplateStep(
            id=id_map[str(s.id)],
            template_id=str(clone.id),
            parent_step_id=id_map.get(str(s.parent_step_id)) if s.parent_step_id else None,
            step_order=int(s.step_order or 1),
            title=s.title,
            description=s.description,
            assignee_type=s.assignee_type,
            assignee_user_id=s.assignee_user_id,
            assignee_role_id=s.assignee_role_id,
            is_required=bool(s.is_required),
        )
        db.add(new_step)

    await db.commit()
    await db.refresh(clone)
    return await _serialize_template(db, clone)


@router.get("/templates/{template_id}/usage")
async def get_template_usage(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    template = await db.get(ApprovalTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    counts = await _instance_counts_for_templates(db, [str(template.id)])
    counts = counts.get(str(template.id)) or {"active": 0, "total": 0}
    return {"active_instances_count": counts["active"], "total_instances_count": counts["total"]}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("roles")),
):
    template = await db.get(ApprovalTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    await db.delete(template)
    await db.commit()
    return {"ok": True}


@router.post("/instances", response_model=ApprovalInstanceResponse)
async def start_instance(
    payload: ApprovalInstanceStart,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    template = await db.get(ApprovalTemplate, str(payload.template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон согласования не найден.")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Шаблон согласования выключен.")
    entity_type = payload.entity_type or template.entity_type
    if entity_type != template.entity_type:
        raise HTTPException(status_code=400, detail="Тип сущности не соответствует шаблону согласования.")
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип сущности.")

    existing_result = await db.execute(
        select(ApprovalInstance).where(
            ApprovalInstance.entity_type == entity_type,
            ApprovalInstance.entity_id == str(payload.entity_id),
            ApprovalInstance.status.in_(INSTANCE_ACTIVE_STATUSES),
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Для этой сущности уже запущено активное согласование.")

    template_steps_result = await db.execute(
        select(ApprovalTemplateStep)
        .where(ApprovalTemplateStep.template_id == str(template.id))
        .order_by(ApprovalTemplateStep.step_order, ApprovalTemplateStep.created_at)
    )
    template_steps = template_steps_result.scalars().all()
    if not template_steps:
        raise HTTPException(status_code=400, detail="Шаблон согласования не содержит ни одного шага.")

    ordered_steps = _order_template_steps(template_steps)
    instance = ApprovalInstance(
        template_id=str(template.id),
        template_name=template.name,
        template_version=template.updated_at or template.created_at,
        entity_type=entity_type,
        entity_id=str(payload.entity_id),
        entity_label=_normalize_text(payload.entity_label),
        status="pending",
        started_by=str(user.id),
    )
    db.add(instance)
    await db.flush()

    instance_steps: List[ApprovalInstanceStep] = []
    first_pending_step: Optional[ApprovalInstanceStep] = None
    for index, (template_step, depth) in enumerate(ordered_steps, start=1):
        status = "pending" if first_pending_step is None else "waiting"
        step = ApprovalInstanceStep(
            instance_id=str(instance.id),
            template_step_id=str(template_step.id),
            parent_template_step_id=str(template_step.parent_step_id) if template_step.parent_step_id else None,
            step_order=index,
            depth=depth,
            title=template_step.title,
            description=template_step.description,
            assignee_type=template_step.assignee_type,
            assignee_user_id=str(template_step.assignee_user_id) if template_step.assignee_user_id else None,
            assignee_role_id=str(template_step.assignee_role_id) if template_step.assignee_role_id else None,
            status=status,
            is_required=bool(template_step.is_required),
        )
        db.add(step)
        await db.flush()
        instance_steps.append(step)
        if first_pending_step is None:
            first_pending_step = step
            instance.current_step_id = str(step.id)

    db.add(
        ApprovalActionLog(
            instance_id=str(instance.id),
            action="started",
            actor_user_id=str(user.id),
            comment=None,
            payload_json={"entity_type": entity_type, "entity_id": str(payload.entity_id)},
        )
    )
    if first_pending_step:
        await _notify_for_step(db, instance, first_pending_step)
    await db.commit()
    await db.refresh(instance)
    return await _serialize_instance(db, instance)


@router.get("/instances", response_model=List[ApprovalInstanceResponse])
async def list_instances(
    request: Request,
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    mine_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    query = select(ApprovalInstance).order_by(ApprovalInstance.started_at.desc())
    if entity_type:
        query = query.where(ApprovalInstance.entity_type == entity_type)
    if entity_id:
        query = query.where(ApprovalInstance.entity_id == entity_id)
    if status:
        query = query.where(ApprovalInstance.status == status)
    if mine_only:
        step_subquery = (
            select(ApprovalInstanceStep.instance_id)
            .where(
                ApprovalInstanceStep.status == "pending",
                or_(
                    and_(
                        ApprovalInstanceStep.assignee_type == "user",
                        ApprovalInstanceStep.assignee_user_id == str(user.id),
                    ),
                    and_(
                        ApprovalInstanceStep.assignee_type == "role",
                        ApprovalInstanceStep.assignee_role_id == str(user.role_id),
                    ),
                ),
            )
        )
        query = query.where(ApprovalInstance.id.in_(step_subquery))
    result = await db.execute(query)
    items = result.scalars().all()
    if not is_superuser(request):
        # M3: non-superusers only see instances they are involved in.
        visible = []
        for item in items:
            if await _user_involved_in_instance(db, item, user):
                visible.append(item)
        items = visible
    users = await _user_map(db)
    roles = await _role_map(db)
    return [await _serialize_instance(db, item, users, roles) for item in items]


@router.get("/inbox", response_model=ApprovalInboxResponse)
async def get_inbox(
    scope: str = Query("pending_me"),
    entity_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    query = select(ApprovalInstance).order_by(ApprovalInstance.started_at.desc())
    if entity_type:
        query = query.where(ApprovalInstance.entity_type == entity_type)
    if status:
        query = query.where(ApprovalInstance.status == status)

    result = await db.execute(query)
    instances = result.scalars().all()
    if not instances:
        return ApprovalInboxResponse(stats=ApprovalInboxStats(), items=[])

    users = await _user_map(db)
    roles = await _role_map(db)
    instance_ids = [str(item.id) for item in instances]

    steps_result = await db.execute(
        select(ApprovalInstanceStep)
        .where(ApprovalInstanceStep.instance_id.in_(instance_ids))
        .order_by(ApprovalInstanceStep.instance_id, ApprovalInstanceStep.step_order, ApprovalInstanceStep.created_at)
    )
    steps_by_instance: Dict[str, List[ApprovalInstanceStep]] = {}
    for step in steps_result.scalars().all():
        steps_by_instance.setdefault(str(step.instance_id), []).append(step)

    visible_items = [
        _build_inbox_item(item, steps_by_instance.get(str(item.id), []), users, roles, user)
        for item in instances
    ]
    visible_items = [item for item in visible_items if item.involved_by_me]

    stats = ApprovalInboxStats(
        pending_me=sum(1 for item in visible_items if item.waiting_for_me and item.status == "pending"),
        active=sum(1 for item in visible_items if item.status == "pending"),
        history=sum(1 for item in visible_items if item.status in {"approved", "rejected", "cancelled"}),
        total_visible=len(visible_items),
    )

    normalized_scope = (scope or "pending_me").strip().lower()
    filtered_items = visible_items
    if normalized_scope == "pending_me":
        filtered_items = [item for item in filtered_items if item.waiting_for_me and item.status == "pending"]
    elif normalized_scope == "active":
        filtered_items = [item for item in filtered_items if item.status == "pending"]
    elif normalized_scope == "history":
        filtered_items = [item for item in filtered_items if item.status in {"approved", "rejected", "cancelled"}]

    normalized_search = (search or "").strip().lower()
    if normalized_search:
        filtered_items = [
            item for item in filtered_items
            if normalized_search in (item.template_name or "").lower()
            or normalized_search in (item.entity_label or "").lower()
            or normalized_search in (item.entity_type_label or "").lower()
            or normalized_search in (item.current_stage_label or "").lower()
            or normalized_search in (item.started_by_label or "").lower()
        ]

    filtered_items.sort(
        key=lambda item: (
            0 if item.waiting_for_me and item.status == "pending" else 1,
            0 if item.status == "pending" else 1,
            -(item.started_at.timestamp() if item.started_at else 0),
        )
    )

    total = len(filtered_items)
    sliced = filtered_items[offset:offset + limit]

    return ApprovalInboxResponse(
        stats=stats,
        items=sliced,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/instances/{instance_id}", response_model=ApprovalInstanceResponse)
async def get_instance(
    instance_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    instance = await db.get(ApprovalInstance, str(instance_id))
    if not instance:
        raise HTTPException(status_code=404, detail="Экземпляр согласования не найден.")
    if not is_superuser(request) and not await _user_involved_in_instance(db, instance, user):
        raise HTTPException(status_code=403, detail="Нет доступа к этому согласованию.")
    return await _serialize_instance(db, instance)


@router.post("/instances/{instance_id}/approve", response_model=ApprovalInstanceResponse)
async def approve_instance_step(
    instance_id: str,
    payload: ApprovalInstanceAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    instance = await db.get(ApprovalInstance, str(instance_id))
    if not instance:
        raise HTTPException(status_code=404, detail="Экземпляр согласования не найден.")
    if instance.status != "pending":
        raise HTTPException(status_code=400, detail="Согласование уже завершено.")

    current_step = None
    if instance.current_step_id:
        current_step = await db.get(ApprovalInstanceStep, str(instance.current_step_id))
    if not current_step or current_step.status != "pending":
        raise HTTPException(status_code=400, detail="У согласования нет активного шага.")
    await _ensure_can_act(current_step, user)

    current_step.status = "approved"
    current_step.acted_by = str(user.id)
    current_step.acted_at = datetime.utcnow()
    current_step.comment = _normalize_text(payload.comment)
    db.add(
        ApprovalActionLog(
            instance_id=str(instance.id),
            instance_step_id=str(current_step.id),
            action="approved",
            actor_user_id=str(user.id),
            comment=current_step.comment,
        )
    )

    next_result = await db.execute(
        select(ApprovalInstanceStep)
        .where(
            ApprovalInstanceStep.instance_id == str(instance.id),
            ApprovalInstanceStep.status == "waiting",
        )
        .order_by(ApprovalInstanceStep.step_order, ApprovalInstanceStep.created_at)
    )
    next_step = next_result.scalars().first()
    if next_step:
        next_step.status = "pending"
        instance.current_step_id = str(next_step.id)
        await _notify_for_step(db, instance, next_step)
    else:
        instance.status = "approved"
        instance.current_step_id = None
        instance.completed_by = str(user.id)
        instance.completed_comment = current_step.comment
        instance.completed_at = datetime.utcnow()
        await _apply_entity_final_effect(db, instance)
    await db.commit()
    await db.refresh(instance)
    return await _serialize_instance(db, instance)


@router.post("/instances/{instance_id}/reject", response_model=ApprovalInstanceResponse)
async def reject_instance_step(
    instance_id: str,
    payload: ApprovalInstanceAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_any_section_access(*AUTHENTICATED_SECTION_KEYS)),
):
    instance = await db.get(ApprovalInstance, str(instance_id))
    if not instance:
        raise HTTPException(status_code=404, detail="Экземпляр согласования не найден.")
    if instance.status != "pending":
        raise HTTPException(status_code=400, detail="Согласование уже завершено.")

    current_step = None
    if instance.current_step_id:
        current_step = await db.get(ApprovalInstanceStep, str(instance.current_step_id))
    if not current_step or current_step.status != "pending":
        raise HTTPException(status_code=400, detail="У согласования нет активного шага.")
    await _ensure_can_act(current_step, user)
    if not _normalize_text(payload.comment):
        raise HTTPException(status_code=400, detail="Для отклонения согласования требуется комментарий.")

    current_step.status = "rejected"
    current_step.acted_by = str(user.id)
    current_step.acted_at = datetime.utcnow()
    current_step.comment = _normalize_text(payload.comment)
    instance.status = "rejected"
    instance.current_step_id = None
    instance.completed_by = str(user.id)
    instance.completed_comment = current_step.comment
    instance.completed_at = datetime.utcnow()
    db.add(
        ApprovalActionLog(
            instance_id=str(instance.id),
            instance_step_id=str(current_step.id),
            action="rejected",
            actor_user_id=str(user.id),
            comment=current_step.comment,
        )
    )
    await db.commit()
    await db.refresh(instance)
    return await _serialize_instance(db, instance)
