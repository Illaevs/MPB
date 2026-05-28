"""
Dashboard summary and activity endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, and_, cast, String, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import (
    Deal,
    DealGip,
    Task,
    OutgoingDocument,
    ContractDocument,
    Contract,
    Document,
    UploadJob,
    Notification,
    RolePermission,
    EventLog,
    User,
)

router = APIRouter()


async def _has_read_all(db: AsyncSession, role_id: Optional[str], section: str) -> bool:
    if not role_id:
        return False
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(role_id),
            RolePermission.section == section,
        )
    )
    perm = result.scalar_one_or_none()
    return bool(perm and perm.read_all)


async def _allowed_deals(db: AsyncSession, user: User, request: Request) -> Optional[List[str]]:
    if getattr(request.state, "is_superuser", False):
        return None
    if await _has_read_all(db, user.role_id, "projects"):
        return None
    result = await db.execute(select(DealGip.deal_id).where(DealGip.user_id == str(user.id)))
    deal_ids = [str(item[0]) for item in result.all()]
    return deal_ids


async def _can_use_manager_dashboard(db: AsyncSession, user: User, request: Request) -> bool:
    if getattr(request.state, "is_superuser", False):
        return True
    for section in ("projects", "tasks", "contracts", "users"):
        if await _has_read_all(db, user.role_id, section):
            return True
    return False


@router.get("/summary")
async def get_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    allowed = await _allowed_deals(db, user, request)
    since = datetime.utcnow() - timedelta(days=7)

    if allowed == []:
        active_deals = 0
        overdue_tasks = 0
        new_documents = 0
    else:
        deal_query = select(func.count(Deal.id)).where(Deal.status == "active")
        if allowed is not None:
            deal_query = deal_query.where(Deal.id.in_(allowed))
        result = await db.execute(deal_query)
        active_deals = int(result.scalar() or 0)

        task_query = select(func.count(Task.id)).where(
            Task.status != "completed",
            Task.due_date.is_not(None),
            Task.due_date < datetime.utcnow().date(),
        )
        if allowed is not None:
            task_query = task_query.where(Task.deal_id.in_(allowed))
        result = await db.execute(task_query)
        overdue_tasks = int(result.scalar() or 0)

        docs_count = 0
        outgoing_query = select(func.count(OutgoingDocument.id)).where(OutgoingDocument.created_at >= since)
        if allowed is not None:
            outgoing_query = outgoing_query.where(OutgoingDocument.deal_id.in_(allowed))
        result = await db.execute(outgoing_query)
        docs_count += int(result.scalar() or 0)

        registry_query = select(func.count(Document.id)).where(Document.created_at >= since)
        if allowed is not None:
            registry_query = registry_query.where(Document.project_id.in_(allowed))
        result = await db.execute(registry_query)
        docs_count += int(result.scalar() or 0)

        contract_query = (
            select(func.count(ContractDocument.id))
            .select_from(ContractDocument)
            .join(Contract, Contract.id == ContractDocument.contract_id)
            .where(ContractDocument.created_at >= since)
        )
        if allowed is not None:
            contract_query = contract_query.where(cast(Contract.deal_id, String).in_(allowed))
        result = await db.execute(contract_query)
        docs_count += int(result.scalar() or 0)

        new_documents = docs_count

    errors_query = select(func.count(UploadJob.id)).where(
        UploadJob.status == "error",
        UploadJob.updated_at.is_not(None),
        UploadJob.updated_at >= since,
    )
    if allowed is not None:
        errors_query = errors_query.where(UploadJob.created_by == str(user.id))
    result = await db.execute(errors_query)
    upload_errors = int(result.scalar() or 0)

    unread_query = select(func.count(Notification.id)).where(
        Notification.user_id == str(user.id),
        Notification.is_read.is_(False),
        (Notification.deliver_at.is_(None)) | (Notification.deliver_at <= func.now()),
    )
    result = await db.execute(unread_query)
    unread_notifications = int(result.scalar() or 0)

    return {
        "active_deals": active_deals,
        "overdue_tasks": overdue_tasks,
        "new_documents_7d": new_documents,
        "upload_errors_7d": upload_errors,
        "unread_notifications": unread_notifications,
    }


@router.get("/activity")
async def get_activity(
    request: Request,
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    allowed = await _allowed_deals(db, user, request)
    if allowed == []:
        return []

    since = datetime.utcnow() - timedelta(days=max(1, days) - 1)
    day_column = func.date(EventLog.created_at)

    query = select(day_column.label("day"), func.count(EventLog.id)).where(EventLog.created_at >= since)
    if allowed is not None:
        query = query.where(
            and_(
                EventLog.entity_type == "deal",
                EventLog.entity_id.in_(allowed),
            )
        )
    query = query.group_by(day_column).order_by(day_column.asc())
    result = await db.execute(query)
    rows = result.all()
    return [{"date": str(day), "count": int(count)} for day, count in rows]


@router.get("/manager-summary")
async def get_manager_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if not await _can_use_manager_dashboard(db, user, request):
        return {
            "enabled": False,
            "active_deals": 0,
            "risky_deals_count": 0,
            "overdue_tasks": 0,
            "unsigned_contracts_count": 0,
            "stalled_contracts_count": 0,
            "overloaded_users_count": 0,
            "risky_deals": [],
            "overloaded_users": [],
            "contracts_on_approval": [],
        }

    allowed = await _allowed_deals(db, user, request)
    if allowed == []:
        return {
            "enabled": True,
            "active_deals": 0,
            "risky_deals_count": 0,
            "overdue_tasks": 0,
            "unsigned_contracts_count": 0,
            "stalled_contracts_count": 0,
            "overloaded_users_count": 0,
            "risky_deals": [],
            "overloaded_users": [],
            "contracts_on_approval": [],
        }

    today = datetime.utcnow().date()
    stalled_since = today - timedelta(days=14)
    open_task_condition = Task.status.notin_(["completed", "cancelled"])
    overdue_task_condition = and_(
        open_task_condition,
        Task.due_date.is_not(None),
        Task.due_date < today,
    )

    deal_query = select(func.count(Deal.id)).where(Deal.status == "active")
    if allowed is not None:
        deal_query = deal_query.where(Deal.id.in_(allowed))
    result = await db.execute(deal_query)
    active_deals = int(result.scalar() or 0)

    overdue_query = select(func.count(Task.id)).where(overdue_task_condition)
    if allowed is not None:
        overdue_query = overdue_query.where(Task.deal_id.in_(allowed))
    result = await db.execute(overdue_query)
    overdue_tasks = int(result.scalar() or 0)

    risky_query = (
        select(
            Deal.id.label("deal_id"),
            Deal.title,
            Deal.address,
            Deal.total_contract_value,
            func.sum(case((open_task_condition, 1), else_=0)).label("open_tasks"),
            func.sum(case((overdue_task_condition, 1), else_=0)).label("overdue_tasks"),
            func.min(
                case(
                    (
                        and_(open_task_condition, Task.due_date.is_not(None)),
                        Task.due_date,
                    ),
                    else_=None,
                )
            ).label("nearest_due_date"),
        )
        .select_from(Deal)
        .outerjoin(Task, Task.deal_id == Deal.id)
        .where(Deal.status == "active")
        .group_by(Deal.id, Deal.title, Deal.address, Deal.total_contract_value)
    )
    if allowed is not None:
        risky_query = risky_query.where(Deal.id.in_(allowed))
    result = await db.execute(risky_query)
    risky_deals_rows = result.all()

    risky_deals = []
    for row in risky_deals_rows:
        open_tasks = int(row.open_tasks or 0)
        overdue_count = int(row.overdue_tasks or 0)
        nearest_due = row.nearest_due_date
        due_soon = bool(nearest_due and 0 <= (nearest_due - today).days <= 7)
        if overdue_count <= 0 and not due_soon:
            continue
        risky_deals.append(
            {
                "id": str(row.deal_id),
                "title": row.title,
                "address": row.address,
                "amount": float(row.total_contract_value or 0),
                "open_tasks": open_tasks,
                "overdue_tasks": overdue_count,
                "nearest_due_date": nearest_due.isoformat() if nearest_due else None,
                "risk_level": "high" if overdue_count > 0 else "medium",
            }
        )
    risky_deals.sort(
        key=lambda item: (
            0 if item["risk_level"] == "high" else 1,
            -item["overdue_tasks"],
            item["nearest_due_date"] or "9999-12-31",
        )
    )
    risky_deals = risky_deals[:6]

    workload_query = (
        select(
            User.id.label("user_id"),
            User.full_name,
            func.sum(case((open_task_condition, 1), else_=0)).label("open_tasks"),
            func.sum(case((overdue_task_condition, 1), else_=0)).label("overdue_tasks"),
        )
        .select_from(Task)
        .join(User, User.id == Task.assigned_to_user_id)
        .where(Task.assigned_to_user_id.is_not(None))
        .group_by(User.id, User.full_name)
        .having(func.sum(case((open_task_condition, 1), else_=0)) > 0)
        .order_by(
            desc(func.sum(case((open_task_condition, 1), else_=0))),
            desc(func.sum(case((overdue_task_condition, 1), else_=0))),
            User.full_name.asc(),
        )
    )
    if allowed is not None:
        workload_query = workload_query.where(Task.deal_id.in_(allowed))
    result = await db.execute(workload_query)
    workload_rows = result.all()

    overloaded_users = []
    overloaded_users_count = 0
    for row in workload_rows:
        open_tasks = int(row.open_tasks or 0)
        overdue_count = int(row.overdue_tasks or 0)
        overloaded = open_tasks >= 5 or overdue_count > 0
        if overloaded:
            overloaded_users_count += 1
        overloaded_users.append(
            {
                "id": str(row.user_id),
                "full_name": row.full_name,
                "open_tasks": open_tasks,
                "overdue_tasks": overdue_count,
                "risk_level": "high" if overdue_count > 0 else ("medium" if open_tasks >= 7 else "normal"),
            }
        )
    overloaded_users = overloaded_users[:6]

    unsigned_query = select(func.count(Contract.id)).where(Contract.status != "completed")
    stalled_query = select(func.count(Contract.id)).where(
        Contract.status == "approval",
        Contract.contract_date <= stalled_since,
    )
    approval_list_query = (
        select(
            Contract.id,
            Contract.contract_number,
            Contract.contract_date,
            Contract.amount,
            Contract.status,
            cast(Contract.deal_id, String).label("deal_id"),
            Deal.title.label("deal_title"),
        )
        .select_from(Contract)
        .outerjoin(Deal, cast(Contract.deal_id, String) == Deal.id)
        .where(Contract.status == "approval")
    )
    if allowed is not None:
        unsigned_query = unsigned_query.where(cast(Contract.deal_id, String).in_(allowed))
        stalled_query = stalled_query.where(cast(Contract.deal_id, String).in_(allowed))
        approval_list_query = approval_list_query.where(cast(Contract.deal_id, String).in_(allowed))
    approval_list_query = approval_list_query.order_by(Contract.contract_date.asc(), Contract.created_at.asc()).limit(6)

    result = await db.execute(unsigned_query)
    unsigned_contracts_count = int(result.scalar() or 0)

    result = await db.execute(stalled_query)
    stalled_contracts_count = int(result.scalar() or 0)

    result = await db.execute(approval_list_query)
    contracts_on_approval = []
    for row in result.all():
        wait_days = (today - row.contract_date).days if row.contract_date else 0
        contracts_on_approval.append(
            {
                "id": str(row.id),
                "contract_number": row.contract_number,
                "contract_date": row.contract_date.isoformat() if row.contract_date else None,
                "deal_id": row.deal_id,
                "deal_title": row.deal_title,
                "amount": float(row.amount or 0),
                "wait_days": wait_days,
                "is_stalled": bool(row.contract_date and row.contract_date <= stalled_since),
            }
        )

    return {
        "enabled": True,
        "active_deals": active_deals,
        "risky_deals_count": len(risky_deals),
        "overdue_tasks": overdue_tasks,
        "unsigned_contracts_count": unsigned_contracts_count,
        "stalled_contracts_count": stalled_contracts_count,
        "overloaded_users_count": overloaded_users_count,
        "risky_deals": risky_deals,
        "overloaded_users": overloaded_users,
        "contracts_on_approval": contracts_on_approval,
    }
