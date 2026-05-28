"""
Work results approvals ("Согласования РР") router.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast
from sqlalchemy.dialects.postgresql import UUID as PgUUID

from app.database.session import get_db
from app.models import StageResult, Deal, Stage, DealGip, User
from app.services.event_log import log_event
from app.services.event_outbox import emit_event_safe


class ResultReviewUpdate(BaseModel):
    status: Optional[str] = None
    reviewer_comment: Optional[str] = None
    reviewer_id: Optional[str] = None


router = APIRouter()


def _normalize_id(value: Optional[str]) -> str:
    if not value:
        return ""
    hex_value = "".join(ch for ch in str(value) if ch.isalnum())
    if len(hex_value) == 32:
        return f"{hex_value[0:8]}-{hex_value[8:12]}-{hex_value[12:16]}-{hex_value[16:20]}-{hex_value[20:32]}"
    return str(value)


def _id_conditions(column, value):
    variants = []
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        variants.extend([parsed, str(parsed), parsed.hex])
    except (ValueError, TypeError):
        variants.append(str(value))

    conditions = []
    if isinstance(column.type, PgUUID):
        column_text = cast(column, String)
        for v in variants:
            if isinstance(v, uuid.UUID):
                conditions.append(column == v)
                conditions.append(column_text == str(v))
            else:
                conditions.append(column_text == str(v))
    else:
        for v in variants:
            conditions.append(column == v)
    return or_(*conditions)


def _version_from_label(label: Optional[str]) -> Optional[int]:
    if not label:
        return None
    parts = label.replace("#", " ").replace("v.", " ").replace("v", " ").split()
    for part in reversed(parts):
        if part.isdigit():
            try:
                return int(part)
            except ValueError:
                return None
    return None


def _serialize_result(item, stage_lookup, deal_lookup, user_by_id=None, user_by_name=None):
    stage = stage_lookup.get(_normalize_id(item.stage_id))
    deal = deal_lookup.get(_normalize_id(item.deal_id))
    version_number = item.version_number or _version_from_label(item.version_label)

    user_by_id = user_by_id or {}
    user_by_name = user_by_name or {}

    reviewer = user_by_id.get(_normalize_id(item.reviewer_id)) if item.reviewer_id else None
    executor = None
    if item.created_by:
        # created_by is stored as a free-form name string; try exact match by full_name
        executor = user_by_name.get(str(item.created_by).strip().lower())

    return {
        "id": item.id,
        "deal_id": item.deal_id,
        "deal_title": deal.title if deal else None,
        "stage_id": item.stage_id,
        "stage_name": stage.name if stage else None,
        "product_name": item.product_name,
        "version_label": item.version_label,
        "version_number": version_number,
        "status": item.status or "review",
        "executor_comment": item.comment,
        "reviewer_comment": item.reviewer_comment,
        "reviewer_id": item.reviewer_id,
        "reviewer_name": reviewer.full_name if reviewer else None,
        "reviewer_avatar_url": reviewer.avatar_url if reviewer else None,
        "reviewed_at": item.reviewed_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "created_by": item.created_by,
        "executor_user_id": executor.id if executor else None,
        "executor_avatar_url": executor.avatar_url if executor else None,
        "public_url": item.public_url,
    }


async def _build_user_lookups(db, items):
    reviewer_ids = {str(item.reviewer_id) for item in items if item.reviewer_id}
    executor_names = {str(item.created_by).strip() for item in items if item.created_by}
    user_by_id = {}
    user_by_name = {}
    if reviewer_ids:
        filters = [_id_conditions(User.id, rid) for rid in reviewer_ids]
        result = await db.execute(select(User).where(or_(*filters)))
        for u in result.scalars().all():
            user_by_id[_normalize_id(u.id)] = u
    if executor_names:
        result = await db.execute(select(User).where(User.full_name.in_(executor_names)))
        for u in result.scalars().all():
            user_by_name[(u.full_name or "").strip().lower()] = u
    return user_by_id, user_by_name


@router.get("/result-reviews")
async def list_result_reviews(
    deal_id: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    only_assigned: bool = Query(False),
    gip_user_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(StageResult)
    if deal_id:
        query = query.where(_id_conditions(StageResult.deal_id, deal_id))
    if product_name:
        query = query.where(StageResult.product_name == product_name)
    if status:
        if status == "review":
            query = query.where(or_(StageResult.status == status, StageResult.status.is_(None)))
        else:
            query = query.where(StageResult.status == status)

    result = await db.execute(query.order_by(StageResult.created_at.desc()))
    items = result.scalars().all()

    if only_assigned and gip_user_id:
        gip_results = await db.execute(select(DealGip.deal_id).where(DealGip.user_id == str(gip_user_id)))
        allowed_deals = {str(item[0]) for item in gip_results.all()}
        allowed_deals = { _normalize_id(item) for item in allowed_deals }
        items = [item for item in items if _normalize_id(item.deal_id) in allowed_deals]

    total = len(items)
    if limit is not None:
        items = items[offset:offset + limit]
    elif offset:
        items = items[offset:]

    stage_ids = {item.stage_id for item in items if item.stage_id}
    deal_ids = {item.deal_id for item in items if item.deal_id}

    stage_lookup = {}
    if stage_ids:
        stage_filters = [_id_conditions(Stage.id, stage_id) for stage_id in stage_ids]
        stage_result = await db.execute(select(Stage).where(or_(*stage_filters)))
        for stage in stage_result.scalars().all():
            stage_lookup[_normalize_id(stage.id)] = stage

    deal_lookup = {}
    if deal_ids:
        deal_filters = [_id_conditions(Deal.id, deal_id) for deal_id in deal_ids]
        deal_result = await db.execute(select(Deal).where(or_(*deal_filters)))
        for deal in deal_result.scalars().all():
            deal_lookup[_normalize_id(deal.id)] = deal

    user_by_id, user_by_name = await _build_user_lookups(db, items)
    payload = [_serialize_result(item, stage_lookup, deal_lookup, user_by_id, user_by_name) for item in items]

    if limit is not None:
        return {"items": payload, "total": total, "offset": offset, "limit": limit}
    return payload


@router.get("/result-reviews/versions")
async def list_result_versions(
    stage_id: str = Query(...),
    product_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(StageResult)
        .where(_id_conditions(StageResult.stage_id, stage_id))
        .where(StageResult.product_name == product_name)
        .order_by(StageResult.created_at.desc())
    )
    result = await db.execute(query)
    items = result.scalars().all()

    stage_ids = {item.stage_id for item in items if item.stage_id}
    deal_ids = {item.deal_id for item in items if item.deal_id}
    stage_lookup = {}
    if stage_ids:
        stage_filters = [_id_conditions(Stage.id, sid) for sid in stage_ids]
        stage_result = await db.execute(select(Stage).where(or_(*stage_filters)))
        for stage in stage_result.scalars().all():
            stage_lookup[_normalize_id(stage.id)] = stage
    deal_lookup = {}
    if deal_ids:
        deal_filters = [_id_conditions(Deal.id, did) for did in deal_ids]
        deal_result = await db.execute(select(Deal).where(or_(*deal_filters)))
        for deal in deal_result.scalars().all():
            deal_lookup[_normalize_id(deal.id)] = deal

    user_by_id, user_by_name = await _build_user_lookups(db, items)
    return [_serialize_result(item, stage_lookup, deal_lookup, user_by_id, user_by_name) for item in items]


@router.patch("/result-reviews/{result_id}")
async def update_result_review(
    result_id: str,
    payload: ResultReviewUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await StageResult.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    allowed = {"review", "approved", "rejected", "send_back"}
    status = payload.status
    reviewer_comment = payload.reviewer_comment
    reviewer_id = payload.reviewer_id

    if status and status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")
    if status in {"rejected", "send_back"} and not reviewer_comment:
        raise HTTPException(status_code=400, detail="Комментарий обязателен при отклонении")

    update_data = {}
    if status:
        update_data["status"] = status
        update_data["reviewed_at"] = datetime.now()
    if reviewer_comment is not None:
        update_data["reviewer_comment"] = reviewer_comment
    if reviewer_id:
        update_data["reviewer_id"] = reviewer_id

    if not update_data:
        return {"message": "No changes"}

    prev_status = result.status
    await StageResult.update(db, result_id, **update_data)
    if result.deal_id:
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(result.deal_id),
                action="result_review.update",
                created_by=str(reviewer_id or ""),
                details={
                    "result_id": str(result.id),
                    "deal_id": str(result.deal_id),
                    "status": status,
                },
            )
        except Exception:
            pass
    # Emit specialized events для SOD-консьюмеров и BI: они хотят слышать
    # именно про переходы review → approved/rejected, не общий update.
    if status and status != prev_status:
        if status == "approved":
            event_type = "stage_result.after_approve"
        elif status in {"rejected", "send_back"}:
            event_type = "stage_result.after_reject"
        elif status == "review":
            event_type = "stage_result.after_submit"
        else:
            event_type = None
        if event_type:
            await emit_event_safe(
                db,
                event_type=event_type,
                entity_type="stage_result",
                entity_id=str(result.id),
                payload={
                    "id": str(result.id),
                    "deal_id": str(result.deal_id) if result.deal_id else None,
                    "stage_id": str(result.stage_id) if result.stage_id else None,
                    "product_name": result.product_name,
                    "version_label": result.version_label,
                    "status_before": prev_status,
                    "status_after": status,
                    "reviewer_id": str(reviewer_id) if reviewer_id else None,
                    "reviewer_comment": reviewer_comment,
                },
                payload_version=1,
            )
    return {"message": "Updated"}
