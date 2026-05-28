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
from app.models import StageResult, Deal, Stage, DealGip
from app.services.event_log import log_event


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


@router.get("/result-reviews")
async def list_result_reviews(
    deal_id: Optional[str] = Query(None),
    product_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    only_assigned: bool = Query(False),
    gip_user_id: Optional[str] = Query(None),
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

    payload = []
    for item in items:
        stage = stage_lookup.get(_normalize_id(item.stage_id))
        deal = deal_lookup.get(_normalize_id(item.deal_id))
        version_number = item.version_number or _version_from_label(item.version_label)
        payload.append(
            {
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
                "reviewed_at": item.reviewed_at,
                "created_at": item.created_at,
                "public_url": item.public_url,
            }
        )

    return payload


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
    return {"message": "Updated"}
