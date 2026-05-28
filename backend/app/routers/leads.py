"""
Leads API Router
"""
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Request, Response, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, desc, asc, cast, String

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models import (
    Lead, LeadProduct, LeadActivity, Deal, DealProduct, Product,
    Task, User, Company,
)
from app.schemas.lead import LeadCreate, LeadResponse
from app.services.permissions import get_section_permissions, ensure_can_edit_record
from app.services.event_log import log_event
from app.services.upload_security import write_upload_to_tmp
from app.services.storage import (
    clean_name,
    ensure_path,
    upload_file_with_safe_extension,
    storage_available,
)

router = APIRouter()


# ---------------- LEAD CRUD + LIST ----------------

@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    responsible_user_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    our_company_id: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_dir: Optional[str] = "desc",
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    try:
        read_all, read_assigned = await get_section_permissions(db, user.role_id, "leads")
        if not read_all:
            if not read_assigned:
                response.headers["X-Total-Count"] = "0"
                return []
            responsible_user_id = str(user.id)

        # Build filter conditions (replicating Lead.get_filtered logic, but composable for count + sort)
        filters = []

        def id_variants(value):
            text = str(value or "").strip()
            if not text:
                return []
            compact = text.replace("-", "").lower()
            values = {text, compact}
            if len(compact) == 32:
                values.add(
                    f"{compact[0:8]}-{compact[8:12]}-{compact[12:16]}-"
                    f"{compact[16:20]}-{compact[20:32]}"
                )
            return list(values)

        if status:
            filters.append(Lead.status == status)
        if responsible_user_id:
            filters.append(Lead.responsible_user_id == responsible_user_id)
        if customer_id:
            cv = id_variants(customer_id)
            if cv:
                filters.append(Lead.customer_id.in_(cv))
        if our_company_id:
            ov = id_variants(our_company_id)
            if ov:
                filters.append(Lead.our_company_id.in_(ov))
        if search and search.strip():
            token = f"%{search.strip()}%"
            filters.append(or_(
                Lead.title.ilike(token),
                Lead.obj_name.ilike(token),
                Lead.address.ilike(token),
            ))

        where_clause = and_(*filters) if filters else None

        # Total count
        count_q = select(func.count(Lead.id))
        if where_clause is not None:
            count_q = count_q.where(where_clause)
        total = (await db.execute(count_q)).scalar() or 0
        response.headers["X-Total-Count"] = str(total)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

        # Sort
        sort_map = {
            "created_at": Lead.created_at,
            "updated_at": Lead.updated_at,
            "title": Lead.title,
            "status": Lead.status,
            "total_value": Lead.total_value,
            "advance_percent": Lead.advance_percent,
        }
        sort_col = sort_map.get(sort_by or "created_at", Lead.created_at)
        order = asc(sort_col) if (sort_dir or "desc").lower() == "asc" else desc(sort_col)

        # Items
        items_q = select(Lead)
        if where_clause is not None:
            items_q = items_q.where(where_clause)
        items_q = items_q.order_by(order).offset(skip).limit(limit)
        items = (await db.execute(items_q)).scalars().all()
        return items
    except Exception as exc:
        print(f"Error getting leads: {exc}")
        response.headers["X-Total-Count"] = "0"
        return []


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    from app.services.our_company import apply_default_our_company
    payload = lead.dict()
    await apply_default_our_company(db, payload)
    item = await Lead.create(db, **payload)
    # Initial timeline event
    try:
        await LeadActivity.create(
            db,
            lead_id=str(item.id),
            activity_type="created",
            content=f"Лид «{item.title}» создан",
            payload={"status": item.status},
            actor_user_id=str(user.id) if user else None,
        )
    except Exception:
        pass
    return item


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "leads")
    if not read_all:
        if not read_assigned or str(lead.responsible_user_id) != str(user.id):
            raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    request: Request,
    lead_update: dict = Body(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    filtered_data = {k: v for k, v in (lead_update or {}).items() if v is not None}
    if not filtered_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    # Detect status change for timeline
    prev = await Lead.get_by_id(db, lead_id)
    if not prev:
        raise HTTPException(status_code=404, detail="Lead not found")
    await ensure_can_edit_record(db, request, user, "leads", prev)
    prev_status = prev.status if prev else None
    lead = await Lead.update(db, lead_id, **filtered_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    new_status = lead.status
    if prev_status and new_status and prev_status != new_status:
        try:
            await LeadActivity.create(
                db,
                lead_id=str(lead.id),
                activity_type="status_change",
                content=f"Статус изменён с «{prev_status}» на «{new_status}»",
                payload={"from": prev_status, "to": new_status},
                actor_user_id=str(user.id) if user else None,
            )
        except Exception:
            pass
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await ensure_can_edit_record(db, request, user, "leads", lead)
    success = await Lead.delete(db, lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.deal_id:
        return {"deal_id": str(lead.deal_id)}

    deal_data = {
        "title": lead.title,
        "obj_name": lead.obj_name,
        "address": lead.address,
        "object_type": lead.object_type,
        "object_area": lead.object_area,
        "customer_id": lead.customer_id,
        "our_company_id": lead.our_company_id,
        "vat_rate": getattr(lead, "vat_rate", None),
        "status": "active",
    }
    deal = await Deal.create(db, **deal_data)

    lead_products = await LeadProduct.get_by_lead(db, str(lead.id))
    for lp in lead_products:
        product = await Product.get_by_id(db, str(lp.product_id))
        if not product:
            continue
        payload = {
            "deal_id": str(deal.id),
            "product_id": str(lp.product_id),
            "custom_name": lp.custom_name,
            "custom_price": lp.custom_price,
            "quantity": lp.quantity,
            "unit": lp.unit or "pcs",
            "unit_price": lp.unit_price,
            "discount_percent": lp.discount_percent,
            "discount_amount": lp.discount_amount,
            "tax_rate": lp.tax_rate,
            "currency": lp.currency,
            "notes": lp.notes,
            "custom_properties": lp.custom_properties or {},
        }
        await DealProduct.create(db, **payload)

    await Deal.calculate_total_value(db, str(deal.id))
    await Lead.update(db, lead_id, status="converted", deal_id=str(deal.id))

    try:
        await LeadActivity.create(
            db,
            lead_id=str(lead.id),
            activity_type="convert",
            content=f"Лид конвертирован в сделку «{deal.title or deal.id}»",
            payload={"deal_id": str(deal.id)},
            actor_user_id=str(user.id) if user else None,
        )
    except Exception:
        pass
    return {"deal_id": str(deal.id)}


# ---------------- TIMELINE / ACTIVITIES ----------------

def _user_to_brief(u: Optional[User]) -> Optional[Dict[str, Any]]:
    if not u:
        return None
    return {
        "id": str(u.id),
        "full_name": u.full_name,
        "email": u.email,
        "avatar_url": u.avatar_url,
    }


async def _enrich_activity(db: AsyncSession, act: LeadActivity, users_cache: Dict[str, User]) -> Dict[str, Any]:
    actor = None
    if act.actor_user_id:
        if act.actor_user_id in users_cache:
            actor = users_cache[act.actor_user_id]
        else:
            u = await User.get_by_id(db, act.actor_user_id) if hasattr(User, "get_by_id") else None
            if not u:
                u = (await db.execute(select(User).where(User.id == act.actor_user_id))).scalar_one_or_none()
            users_cache[act.actor_user_id] = u
            actor = u

    payload = act.payload or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    # If task_link, enrich with task brief
    if act.activity_type == "task_link" and payload.get("task_id"):
        task = (await db.execute(select(Task).where(Task.id == str(payload["task_id"])))).scalar_one_or_none()
        if task:
            payload = {
                **payload,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                }
            }

    return {
        "id": str(act.id),
        "lead_id": str(act.lead_id),
        "activity_type": act.activity_type,
        "content": act.content,
        "payload": payload,
        "created_at": act.created_at,
        "actor": _user_to_brief(actor),
    }


@router.get("/{lead_id}/timeline")
async def get_lead_timeline(
    lead_id: str,
    limit: int = 200,
    offset: int = 0,
    types: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(CurrentUser),
):
    """Return timeline activities for a lead. `types` is a comma-separated filter."""
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    query = (
        select(LeadActivity)
        .where(LeadActivity.lead_id == str(lead.id))
        .order_by(LeadActivity.created_at.desc())
    )
    if types:
        wanted = [t.strip() for t in types.split(",") if t.strip()]
        if wanted:
            query = query.where(LeadActivity.activity_type.in_(wanted))
    query = query.offset(offset).limit(limit)

    rows = (await db.execute(query)).scalars().all()
    users_cache: Dict[str, User] = {}
    return [await _enrich_activity(db, act, users_cache) for act in rows]


@router.post("/{lead_id}/comments")
async def add_lead_comment(
    lead_id: str,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    content = (body or {}).get("content") or ""
    if not content.strip():
        raise HTTPException(status_code=400, detail="Empty comment")
    act = await LeadActivity.create(
        db,
        lead_id=str(lead.id),
        activity_type="comment",
        content=content.strip(),
        payload={},
        actor_user_id=str(user.id) if user else None,
    )
    users_cache: Dict[str, User] = {}
    return await _enrich_activity(db, act, users_cache)


@router.post("/{lead_id}/files")
async def upload_lead_file(
    lead_id: str,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage not configured")

    folder = f"leads/{lead.id}/files"
    await ensure_path(folder)
    safe_name = clean_name(file.filename or "file")
    file_path = f"{folder}/{safe_name}"

    # Write upload to tmp then upload to storage
    tmp_path, size = await write_upload_to_tmp(file)
    try:
        await upload_file_with_safe_extension(file_path, tmp_path)
    finally:
        try:
            import os
            os.unlink(tmp_path)
        except Exception:
            pass

    act = await LeadActivity.create(
        db,
        lead_id=str(lead.id),
        activity_type="file",
        content=(caption or "").strip() or safe_name,
        payload={
            "file_name": safe_name,
            "file_path": file_path,
            "file_size": size,
            "content_type": file.content_type,
        },
        actor_user_id=str(user.id) if user else None,
    )
    users_cache: Dict[str, User] = {}
    return await _enrich_activity(db, act, users_cache)


@router.post("/{lead_id}/tasks")
async def create_lead_task(
    lead_id: str,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    """Create a task linked to this lead and add a timeline entry."""
    lead = await Lead.get_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    title = (body or {}).get("title")
    if not title or not str(title).strip():
        raise HTTPException(status_code=400, detail="Title is required")

    payload = {
        "title": str(title).strip(),
        "description": (body or {}).get("description"),
        "status": (body or {}).get("status", "new"),
        "priority": (body or {}).get("priority", "normal"),
        "due_date": (body or {}).get("due_date"),
        "assigned_to_user_id": (body or {}).get("assigned_to_user_id"),
        "lead_id": str(lead.id),
        "created_by_user_id": str(user.id) if user else None,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    task = await Task.create(db, **payload)

    act = await LeadActivity.create(
        db,
        lead_id=str(lead.id),
        activity_type="task_link",
        content=f"Создана задача «{task.title}»",
        payload={"task_id": str(task.id)},
        actor_user_id=str(user.id) if user else None,
    )
    users_cache: Dict[str, User] = {}
    return await _enrich_activity(db, act, users_cache)


@router.delete("/activities/{activity_id}")
async def delete_lead_activity(
    activity_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    act = (await db.execute(select(LeadActivity).where(LeadActivity.id == str(activity_id)))).scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    # Only allow deletion of comments (and own files) by the author or superuser
    if act.activity_type not in {"comment", "file"}:
        raise HTTPException(status_code=400, detail="System activities cannot be deleted")
    if act.actor_user_id and user and str(act.actor_user_id) != str(user.id):
        # TODO: superuser bypass
        raise HTTPException(status_code=403, detail="Not author")
    await LeadActivity.delete(db, str(activity_id))
    return {"ok": True}
