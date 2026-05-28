"""
Deal execution (de-jure / de-facto) API router.
"""
import uuid
import logging
from contextlib import suppress
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models import (
    Deal,
    Contract,
    SubcontractorCard,
    SubcontractorProduct,
    SubcontractorStage,
    DealProduct,
    Stage,
    StageProductAssignment,
    StageProductSubtask,
    StageProductLink,
    Product,
    StageResult,
)
from app.schemas.stage_product_assignment import (
    StageProductAssignmentCreate,
    StageProductAssignmentUpdate,
    StageProductAssignmentResponse,
)
from app.schemas.stage_product_subtask import (
    StageProductSubtaskCreate,
    StageProductSubtaskUpdate,
    StageProductSubtaskResponse,
)
from app.services.data_health import safe_refresh_deal_health_issues
from app.services.event_outbox import emit_event_safe


router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_SUBTASK_TITLES = [
    "ТЗ",
    "ИД",
    "ПЗ",
    "Пояснительная записка",
]


def _normalize_name(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _normalize_uuid_like(value):
    if value in (None, ""):
        return ""
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return parsed.hex
    except (ValueError, TypeError):
        return str(value)


def _id_conditions(column, value):
    variants = []
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        variants.extend([parsed, str(parsed), parsed.hex])
    except (ValueError, TypeError):
        variants.append(str(value))
    return or_(*[column == v for v in variants])


def _id_variants(*values):
    variants = []
    seen = set()
    for value in values:
        if value is None:
            continue
        current = []
        try:
            parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
            current.extend([parsed, str(parsed), parsed.hex])
        except (ValueError, TypeError):
            current.append(str(value))
        for item in current:
            key = str(item)
            if key in seen:
                continue
            seen.add(key)
            variants.append(item)
    return variants


def _id_in_conditions(column, values):
    variants = [str(v) for v in _id_variants(*values)]
    if not variants:
        return cast(column, String).in_(["__never_match__"])
    return cast(column, String).in_(variants)


def _version_from_label(label: str):
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


@router.get("/deals/{deal_id}/dejure")
async def get_dejure_view(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
):
    deal = await Deal.get_by_id(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    contracts = await Contract.get_by_deal_id(db, deal_id)
    cards_map: Dict[str, Dict] = {}

    for contract in contracts:
        if not contract.subcontractor_card_id:
            continue
        card = cards_map.get(str(contract.subcontractor_card_id))
        if not card:
            card_obj = await SubcontractorCard.get_by_id(db, str(contract.subcontractor_card_id))
            if not card_obj:
                continue
            card = {
                "id": card_obj.id,
                "title": card_obj.title,
                "obj_name": card_obj.obj_name,
                "address": card_obj.address,
                "contracts": [],
            }
            cards_map[str(card_obj.id)] = card

        products_result = await db.execute(
            select(SubcontractorProduct)
            .options(selectinload(SubcontractorProduct.product))
            .where(_id_conditions(SubcontractorProduct.contract_id, contract.id))
        )
        products = products_result.scalars().all()

        stages_result = await db.execute(
            select(SubcontractorStage).where(_id_conditions(SubcontractorStage.contract_id, contract.id))
        )
        stages = stages_result.scalars().all()

        card["contracts"].append(
            {
                "id": str(contract.id),
                "contract_number": contract.contract_number,
                "contract_date": contract.contract_date,
                "status": contract.status,
                "amount": contract.amount,
                "contract_type": contract.contract_type,
                "products": [
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "name": item.custom_name or (item.product.name if item.product else ""),
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "unit_price": item.unit_price,
                        "tax_rate": item.tax_rate,
                        "total_price": item.total_price,
                        "status": item.status,
                        "stage_id": str(item.stage_id) if item.stage_id else None,
                    }
                    for item in products
                ],
                "stages": [
                    {
                        "id": str(stage.id),
                        "name": stage.name,
                        "description": stage.description,
                        "stage_type": stage.stage_type,
                        "term_type": stage.term_type,
                        "duration": stage.duration,
                        "date_start": stage.date_start,
                        "date_end": stage.date_end,
                        "close_date": stage.close_date,
                        "planned_cost": stage.planned_cost,
                        "actual_cost": stage.actual_cost,
                        "status": stage.status,
                        "subcontractor_card_id": stage.subcontractor_card_id,
                        "contract_id": stage.contract_id,
                    }
                    for stage in stages
                ],
            }
        )

    return {"deal_id": deal.id, "subcontractors": list(cards_map.values())}


@router.get("/deals/{deal_id}/defacto")
async def get_defacto_view(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
):
    deal = await Deal.get_by_id(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal_products = await DealProduct.get_by_deal(db, deal_id)
    deal_products_map = {str(item.id): item for item in deal_products}

    links = await StageProductLink.get_by_deal(db, deal_id)
    stage_products_map: Dict[str, list] = {}
    stage_ids = set()
    for link in links:
        stage_id = _normalize_uuid_like(link.stage_id)
        deal_product = deal_products_map.get(str(link.deal_product_id))
        if not deal_product:
            continue
        stage_ids.add(stage_id)
        stage_products_map.setdefault(stage_id, []).append(deal_product)

    if not stage_ids:
        return {"deal_id": deal.id, "stages": []}

    stages = await Stage.get_by_deal_id(db, deal_id)
    stage_lookup = {_normalize_uuid_like(stage.id): stage for stage in stages}
    stage_ids = {stage_id for stage_id in stage_ids if stage_id in stage_lookup}
    if not stage_ids:
        return {"deal_id": deal.id, "stages": []}

    contracts = await Contract.get_by_deal_id(db, deal_id)
    contracts = [contract for contract in contracts if contract.subcontractor_card_id]
    contract_ids = [str(contract.id) for contract in contracts]

    subcontractor_products: List[SubcontractorProduct] = []
    if contract_ids:
        subproducts_result = await db.execute(
            select(SubcontractorProduct)
            .options(selectinload(SubcontractorProduct.product))
            .where(_id_in_conditions(SubcontractorProduct.contract_id, contract_ids))
        )
        subcontractor_products = subproducts_result.scalars().all()

    subcontractor_by_product: Dict[str, list] = {}
    subcontractor_by_name: Dict[str, list] = {}
    subcontractor_lookup: Dict[str, SubcontractorProduct] = {}
    for item in subcontractor_products:
        subcontractor_lookup[_normalize_uuid_like(item.id)] = item
        subcontractor_by_product.setdefault(_normalize_uuid_like(item.product_id), []).append(item)
        name = item.custom_name or (item.product.name if item.product else "")
        normalized = _normalize_name(name)
        if normalized:
            subcontractor_by_name.setdefault(normalized, []).append(item)

    assignments_result = await db.execute(
        select(StageProductAssignment).where(_id_conditions(StageProductAssignment.deal_id, deal.id))
    )
    assignments_raw = assignments_result.scalars().all()
    assignments: List[StageProductAssignment] = []
    assignment_keys = {
        ()
    }
    assignment_keys = set()
    duplicate_assignments: List[StageProductAssignment] = []
    for assignment in sorted(
        assignments_raw,
        key=lambda item: ((item.created_at.isoformat() if item.created_at else ""), str(item.id)),
    ):
        key = (
            _normalize_uuid_like(assignment.stage_id),
            _normalize_uuid_like(assignment.product_id),
            _normalize_uuid_like(assignment.subcontractor_card_id),
            _normalize_uuid_like(assignment.contract_id),
            _normalize_uuid_like(assignment.subcontractor_product_id),
        )
        if key in assignment_keys:
            duplicate_assignments.append(assignment)
            continue
        assignment_keys.add(key)
        assignments.append(assignment)

    if duplicate_assignments:
        duplicate_ids = [assignment.id for assignment in duplicate_assignments]
        await db.execute(delete(StageProductSubtask).where(_id_in_conditions(StageProductSubtask.assignment_id, duplicate_ids)))
        await db.execute(delete(StageProductAssignment).where(_id_in_conditions(StageProductAssignment.id, duplicate_ids)))
        await db.commit()

    for stage_id in stage_ids:
        stage = stage_lookup.get(stage_id)
        for deal_product in stage_products_map.get(stage_id, []):
            product_name = deal_product.custom_name or (deal_product.product.name if deal_product.product else "")
            normalized_product_name = _normalize_name(product_name)
            matches = subcontractor_by_name.get(normalized_product_name, [])
            if not matches:
                matches = subcontractor_by_product.get(_normalize_uuid_like(deal_product.product_id), [])
            for subproduct in matches:
                key = (
                    stage_id,
                    _normalize_uuid_like(deal_product.product_id),
                    _normalize_uuid_like(subproduct.subcontractor_card_id),
                    _normalize_uuid_like(subproduct.contract_id),
                    _normalize_uuid_like(subproduct.id),
                )
                if key in assignment_keys:
                    continue
                try:
                    assignment = await StageProductAssignment.create(
                        db,
                        deal_id=str(deal.id),
                        stage_id=stage_id,
                        product_id=str(deal_product.product_id),
                        subcontractor_card_id=str(subproduct.subcontractor_card_id),
                        subcontractor_product_id=str(subproduct.id),
                        contract_id=str(subproduct.contract_id) if subproduct.contract_id else None,
                        start_date=stage.date_start if stage else None,
                        due_date=stage.date_end if stage else None,
                        contract_due_date=stage.date_end if stage else None,
                        status="not_started",
                    )
                except Exception:
                    logger.exception(
                        "Defacto: failed to create assignment",
                        extra={
                            "deal_id": str(deal.id),
                            "stage_id": stage_id,
                            "product_id": str(deal_product.product_id),
                            "subcontractor_card_id": str(subproduct.subcontractor_card_id),
                            "subcontractor_product_id": str(subproduct.id),
                            "contract_id": str(subproduct.contract_id) if subproduct.contract_id else None,
                        },
                    )
                    with suppress(Exception):
                        await db.rollback()
                    continue
                assignments.append(assignment)
                assignment_keys.add(key)
                for title in DEFAULT_SUBTASK_TITLES:
                    try:
                        await StageProductSubtask.create(
                            db,
                            assignment_id=assignment.id,
                            title=title,
                            status="not_started",
                        )
                    except Exception:
                        logger.exception(
                            "Defacto: failed to create subtask",
                            extra={
                                "assignment_id": assignment.id,
                                "title": title,
                            },
                        )
                        with suppress(Exception):
                            await db.rollback()

    assignment_ids = [assignment.id for assignment in assignments]
    subtasks_map: Dict[str, list] = {}
    if assignment_ids:
        subtasks_result = await db.execute(
            select(StageProductSubtask).where(
                _id_in_conditions(StageProductSubtask.assignment_id, assignment_ids)
            )
        )
        for subtask in subtasks_result.scalars().all():
            subtasks_map.setdefault(str(subtask.assignment_id), []).append(subtask)

    card_ids = {str(assignment.subcontractor_card_id) for assignment in assignments if assignment.subcontractor_card_id}
    card_lookup: Dict[str, SubcontractorCard] = {}
    if card_ids:
        cards_result = await db.execute(
            select(SubcontractorCard).where(_id_in_conditions(SubcontractorCard.id, card_ids))
        )
        cards = cards_result.scalars().all()
        card_lookup = {str(card.id): card for card in cards}

    assignments_by_deal_product: Dict[str, list] = {}
    assignments_by_product_key: Dict[str, list] = {}
    for assignment in assignments:
        stage_key = _normalize_uuid_like(assignment.stage_id)
        product_key = _normalize_uuid_like(assignment.product_id)
        stage_deal_products = stage_products_map.get(stage_key, [])
        matched_deal_product_id = None

        subproduct_name = ""
        if assignment.subcontractor_product_id:
            subproduct = subcontractor_lookup.get(_normalize_uuid_like(assignment.subcontractor_product_id))
            if subproduct:
                subproduct_name = _normalize_name(subproduct.custom_name or (subproduct.product.name if subproduct.product else ""))

        if subproduct_name:
            exact_name_matches = [
                deal_product
                for deal_product in stage_deal_products
                if _normalize_name(deal_product.custom_name or (deal_product.product.name if deal_product.product else "")) == subproduct_name
            ]
            if len(exact_name_matches) == 1:
                matched_deal_product_id = str(exact_name_matches[0].id)

        if not matched_deal_product_id:
            same_product_matches = [
                deal_product
                for deal_product in stage_deal_products
                if _normalize_uuid_like(deal_product.product_id) == product_key
            ]
            if len(same_product_matches) == 1:
                matched_deal_product_id = str(same_product_matches[0].id)

        if matched_deal_product_id:
            assignments_by_deal_product.setdefault(matched_deal_product_id, []).append(assignment)
        else:
            fallback_key = f"{stage_key}:{product_key}"
            assignments_by_product_key.setdefault(fallback_key, []).append(assignment)

    # Latest stage results per stage + product
    latest_results = {}
    if stage_ids:
        result_query = select(StageResult).where(_id_in_conditions(StageResult.stage_id, stage_ids))
        results = (await db.execute(result_query)).scalars().all()
        for result in results:
            stage_key = _normalize_stage_id(result.stage_id)
            product_key = _normalize_name(result.product_name)
            key = f"{stage_key}:{product_key}"
            current = latest_results.get(key)
            current_version = None
            if current:
                current_version = current.version_number or _version_from_label(current.version_label)
            next_version = result.version_number or _version_from_label(result.version_label)
            if not current:
                latest_results[key] = result
                continue
            if next_version and (not current_version or next_version > current_version):
                latest_results[key] = result
                continue
            if result.created_at and current.created_at and result.created_at > current.created_at:
                latest_results[key] = result

    response_stages = []
    for stage_id in stage_ids:
        stage = stage_lookup.get(stage_id)
        if not stage:
            continue
        products_payload = []
        for deal_product in stage_products_map.get(stage_id, []):
            name = deal_product.custom_name or (deal_product.product.name if deal_product.product else "")
            fallback_key = f"{stage_id}:{_normalize_uuid_like(deal_product.product_id)}"
            assign_payload = []
            deal_product_assignments = assignments_by_deal_product.get(str(deal_product.id))
            if deal_product_assignments is None:
                deal_product_assignments = assignments_by_product_key.get(fallback_key, [])
            for assignment in deal_product_assignments:
                card = card_lookup.get(str(assignment.subcontractor_card_id))
                assign_payload.append(
                    {
                        "id": assignment.id,
                        "subcontractor_card_id": assignment.subcontractor_card_id,
                        "subcontractor_name": card.title if card else "",
                        "start_date": assignment.start_date,
                        "due_date": assignment.due_date,
                        "contract_due_date": assignment.contract_due_date,
                        "status": assignment.status,
                        "contract_id": assignment.contract_id,
                        "subcontractor_product_id": assignment.subcontractor_product_id,
                        "subtasks": [
                            {
                                "id": task.id,
                                "title": task.title,
                                "due_date": task.due_date,
                                "status": task.status,
                            }
                            for task in subtasks_map.get(str(assignment.id), [])
                        ],
                    }
                )
            products_payload.append(
                {
                    "deal_product_id": deal_product.id,
                    "product_id": deal_product.product_id,
                    "name": name,
                    "quantity": deal_product.quantity,
                    "unit": deal_product.unit,
                    "unit_price": deal_product.unit_price,
                    "total_price": deal_product.total_price,
                    "assignments": assign_payload,
                    "latest_result": None,
                }
            )
            result_key = f"{stage_id}:{_normalize_name(name)}"
            latest = latest_results.get(result_key)
            if latest:
                products_payload[-1]["latest_result"] = {
                    "id": latest.id,
                    "status": latest.status or "review",
                    "version_label": latest.version_label,
                    "version_number": latest.version_number or _version_from_label(latest.version_label),
                    "executor_comment": latest.comment,
                    "reviewer_comment": latest.reviewer_comment,
                    "reviewed_at": latest.reviewed_at,
                    "created_at": latest.created_at,
                    "public_url": latest.public_url,
                }
        response_stages.append(
            {
                "id": stage.id,
                "name": stage.name,
                "date_start": stage.date_start,
                "date_end": stage.date_end,
                "status": stage.status,
                "products": products_payload,
            }
        )

    response_stages.sort(
        key=lambda item: item["date_start"].isoformat() if item["date_start"] else ""
    )
    return {"deal_id": deal.id, "stages": response_stages}


@router.post("/defacto/assignments", response_model=StageProductAssignmentResponse)
async def create_assignment(
    payload: StageProductAssignmentCreate,
    db: AsyncSession = Depends(get_db),
):
    deal = await Deal.get_by_id(db, str(payload.deal_id))
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    stage = await Stage.get_by_id(db, str(payload.stage_id))
    if not stage or str(stage.deal_id) != str(deal.id):
        raise HTTPException(status_code=400, detail="Stage does not belong to deal")

    product = await Product.get_by_id(db, str(payload.product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    card = await SubcontractorCard.get_by_id(db, str(payload.subcontractor_card_id))
    if not card:
        raise HTTPException(status_code=404, detail="Subcontractor card not found")

    item_data = payload.dict()
    if payload.subcontractor_product_id and not payload.contract_id:
        sub_prod = await SubcontractorProduct.get_by_id(db, str(payload.subcontractor_product_id))
        if sub_prod and sub_prod.contract_id:
            item_data["contract_id"] = sub_prod.contract_id

    assignment = await StageProductAssignment.create(db, **item_data)
    await safe_refresh_deal_health_issues(db, assignment.deal_id)
    await emit_event_safe(
        db,
        event_type="stage_product_assignment.after_create",
        entity_type="stage_product_assignment",
        entity_id=str(assignment.id),
        payload={
            "id": str(assignment.id),
            "deal_id": str(assignment.deal_id) if assignment.deal_id else None,
            "stage_id": str(assignment.stage_id) if assignment.stage_id else None,
            "product_id": str(assignment.product_id) if assignment.product_id else None,
            "subcontractor_card_id": str(assignment.subcontractor_card_id) if assignment.subcontractor_card_id else None,
            "contract_id": str(assignment.contract_id) if assignment.contract_id else None,
        },
        payload_version=1,
    )
    return assignment


@router.put("/defacto/assignments/{assignment_id}", response_model=StageProductAssignmentResponse)
async def update_assignment(
    assignment_id: str,
    payload: StageProductAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    update_payload = payload.dict(exclude_unset=True)
    assignment = await StageProductAssignment.update(db, assignment_id, **update_payload)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await safe_refresh_deal_health_issues(db, assignment.deal_id)
    await emit_event_safe(
        db,
        event_type="stage_product_assignment.after_update",
        entity_type="stage_product_assignment",
        entity_id=str(assignment.id),
        payload={
            "id": str(assignment.id),
            "deal_id": str(assignment.deal_id) if assignment.deal_id else None,
            "stage_id": str(assignment.stage_id) if assignment.stage_id else None,
            "changed_fields": list(update_payload.keys()),
        },
        payload_version=1,
    )
    return assignment


@router.delete("/defacto/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
):
    assignment = await StageProductAssignment.get_by_id(db, assignment_id)
    deal_id = str(assignment.deal_id) if assignment and assignment.deal_id else None
    stage_id = str(assignment.stage_id) if assignment and assignment.stage_id else None
    success = await StageProductAssignment.delete(db, assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await safe_refresh_deal_health_issues(db, assignment.deal_id if assignment else None)
    await emit_event_safe(
        db,
        event_type="stage_product_assignment.after_delete",
        entity_type="stage_product_assignment",
        entity_id=str(assignment_id),
        payload={
            "id": str(assignment_id),
            "deal_id": deal_id,
            "stage_id": stage_id,
        },
        payload_version=1,
    )
    return {"message": "Assignment deleted"}


@router.get("/defacto/assignments/{assignment_id}/subtasks", response_model=List[StageProductSubtaskResponse])
async def list_subtasks(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StageProductSubtask).where(_id_conditions(StageProductSubtask.assignment_id, assignment_id))
    )
    return result.scalars().all()


@router.post("/defacto/assignments/{assignment_id}/subtasks/auto", response_model=List[StageProductSubtaskResponse])
async def auto_create_subtasks(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
):
    assignment = await StageProductAssignment.get_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    existing = await db.execute(
        select(StageProductSubtask).where(_id_conditions(StageProductSubtask.assignment_id, assignment_id))
    )
    if existing.scalars().first():
        return []

    created = []
    for title in DEFAULT_SUBTASK_TITLES:
        created.append(
            await StageProductSubtask.create(
                db,
                assignment_id=assignment_id,
                title=title,
                status="not_started",
            )
        )
    await safe_refresh_deal_health_issues(db, assignment.deal_id)
    return created


@router.post("/defacto/subtasks", response_model=StageProductSubtaskResponse)
async def create_subtask(
    payload: StageProductSubtaskCreate,
    db: AsyncSession = Depends(get_db),
):
    subtask = await StageProductSubtask.create(db, **payload.dict())
    assignment = await StageProductAssignment.get_by_id(db, str(subtask.assignment_id))
    await safe_refresh_deal_health_issues(db, assignment.deal_id if assignment else None)
    return subtask


@router.put("/defacto/subtasks/{subtask_id}", response_model=StageProductSubtaskResponse)
async def update_subtask(
    subtask_id: str,
    payload: StageProductSubtaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    subtask = await StageProductSubtask.update(db, subtask_id, **payload.dict(exclude_unset=True))
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    assignment = await StageProductAssignment.get_by_id(db, str(subtask.assignment_id))
    await safe_refresh_deal_health_issues(db, assignment.deal_id if assignment else None)
    return subtask


@router.delete("/defacto/subtasks/{subtask_id}")
async def delete_subtask(
    subtask_id: str,
    db: AsyncSession = Depends(get_db),
):
    subtask = await StageProductSubtask.get_by_id(db, subtask_id)
    assignment = await StageProductAssignment.get_by_id(db, str(subtask.assignment_id)) if subtask else None
    success = await StageProductSubtask.delete(db, subtask_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subtask not found")
    await safe_refresh_deal_health_issues(db, assignment.deal_id if assignment else None)
    return {"message": "Subtask deleted"}
