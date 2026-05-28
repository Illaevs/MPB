"""
Executor panel endpoints.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import String, cast, delete, select, and_, or_
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models.subcontractor_card import SubcontractorCard
from app.models.stage import Stage
from app.models.deal import Deal
from app.models.deal_product import DealProduct
from app.models.contract import Contract
from app.models.company_user_link import CompanyUserLink
from app.models.subcontractor_product import SubcontractorProduct
from app.models.stage_product_link import StageProductLink
from app.models.stage_result import StageResult
from app.models.stage_product_assignment import StageProductAssignment
from app.models.stage_product_subtask import StageProductSubtask
from app.services.storage import (
    storage_available,
    clean_name,
    ensure_path,
    list_items,
    publish,
    get_download_href,
    upload_bytes_with_safe_extension,
    delete_path,
)
from app.core.config import settings


router = APIRouter()

DEFAULT_SUBTASK_TITLES = [
    "TZ",
    "ID",
    "WORKS",
    "RESULTS",
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


async def _dedupe_assignments(db: AsyncSession, assignments: List[StageProductAssignment]) -> List[StageProductAssignment]:
    unique_assignments: List[StageProductAssignment] = []
    assignment_keys = set()
    duplicate_assignments: List[StageProductAssignment] = []

    for assignment in sorted(
        assignments,
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
        unique_assignments.append(assignment)

    if duplicate_assignments:
        duplicate_ids = [assignment.id for assignment in duplicate_assignments]
        await db.execute(
            delete(StageProductSubtask).where(_id_in_conditions(StageProductSubtask.assignment_id, duplicate_ids))
        )
        await db.execute(
            delete(StageProductAssignment).where(_id_in_conditions(StageProductAssignment.id, duplicate_ids))
        )
        await db.commit()

    return unique_assignments


async def _ensure_assignments_for_card(
    db: AsyncSession,
    subcontractor_card_id: str,
    deal_id: Optional[str] = None,
    stage_id: Optional[str] = None,
):
    contracts = await Contract.get_by_subcontractor_card_id(db, subcontractor_card_id)
    if deal_id:
        contracts = [contract for contract in contracts if str(contract.deal_id) == str(deal_id)]
    if not contracts:
        return

    contract_ids = [str(contract.id) for contract in contracts]
    deal_ids = {str(contract.deal_id) for contract in contracts if contract.deal_id}
    if deal_id:
        deal_ids = {str(deal_id)}

    contract_filters = [_id_conditions(SubcontractorProduct.contract_id, cid) for cid in contract_ids]
    subproducts_result = await db.execute(
        select(SubcontractorProduct)
        .options(selectinload(SubcontractorProduct.product))
        .where(or_(*contract_filters))
    )
    subcontractor_products = subproducts_result.scalars().all()

    subproducts_by_product = {}
    subproducts_by_name = {}
    for item in subcontractor_products:
        subproducts_by_product.setdefault(_normalize_uuid_like(item.product_id), []).append(item)
        name = item.custom_name or (item.product.name if item.product else "")
        normalized = _normalize_name(name)
        if normalized:
            subproducts_by_name.setdefault(normalized, []).append(item)

    for current_deal_id in deal_ids:
        deal_products = await DealProduct.get_by_deal(db, current_deal_id)
        deal_products_map = {
            _normalize_uuid_like(item.id): item for item in deal_products
        }

        links = await StageProductLink.get_by_deal(db, current_deal_id)
        if stage_id:
            normalized_stage_id = _normalize_uuid_like(stage_id)
            links = [link for link in links if _normalize_uuid_like(link.stage_id) == normalized_stage_id]
        if not links:
            continue

        stage_uuid_list = []
        for link in links:
            try:
                stage_uuid_list.append(uuid.UUID(str(link.stage_id)))
            except (ValueError, TypeError):
                continue

        stage_lookup = {}
        if stage_uuid_list:
            stage_result = await db.execute(select(Stage).where(Stage.id.in_(stage_uuid_list)))
            stage_lookup = {_normalize_uuid_like(stage.id): stage for stage in stage_result.scalars().all()}

        assignments_result = await db.execute(
            select(StageProductAssignment).where(
                _id_conditions(StageProductAssignment.subcontractor_card_id, subcontractor_card_id),
                _id_conditions(StageProductAssignment.deal_id, current_deal_id),
            )
        )
        assignments = await _dedupe_assignments(db, assignments_result.scalars().all())
        assignment_keys = {
            (
                _normalize_uuid_like(item.stage_id),
                _normalize_uuid_like(item.product_id),
                _normalize_uuid_like(item.subcontractor_card_id),
                _normalize_uuid_like(item.contract_id),
                _normalize_uuid_like(item.subcontractor_product_id),
            )
            for item in assignments
        }

        for link in links:
            deal_product = deal_products_map.get(_normalize_uuid_like(link.deal_product_id))
            if not deal_product:
                continue
            name = deal_product.custom_name or (deal_product.product.name if deal_product.product else "")
            matches = subproducts_by_name.get(_normalize_name(name), [])
            if not matches:
                matches = subproducts_by_product.get(_normalize_uuid_like(deal_product.product_id), [])
            for subproduct in matches:
                if str(subproduct.subcontractor_card_id) != str(subcontractor_card_id):
                    continue
                key = (
                    _normalize_uuid_like(link.stage_id),
                    _normalize_uuid_like(deal_product.product_id),
                    _normalize_uuid_like(subproduct.subcontractor_card_id),
                    _normalize_uuid_like(subproduct.contract_id),
                    _normalize_uuid_like(subproduct.id),
                )
                if key in assignment_keys:
                    continue
                stage = stage_lookup.get(_normalize_uuid_like(link.stage_id))
                assignment = await StageProductAssignment.create(
                    db,
                    deal_id=str(current_deal_id),
                    stage_id=str(link.stage_id),
                    product_id=str(deal_product.product_id),
                    subcontractor_card_id=str(subcontractor_card_id),
                    subcontractor_product_id=str(subproduct.id),
                    contract_id=str(subproduct.contract_id) if subproduct.contract_id else None,
                    start_date=stage.date_start if stage else None,
                    due_date=stage.date_end if stage else None,
                    contract_due_date=stage.date_end if stage else None,
                    status="not_started",
                )
                assignment_keys.add(key)
                for title in DEFAULT_SUBTASK_TITLES:
                    await StageProductSubtask.create(
                        db,
                        assignment_id=assignment.id,
                        title=title,
                        status="not_started",
                    )


async def _find_matching_deal(db: AsyncSession, card: SubcontractorCard) -> Optional[Deal]:
    from sqlalchemy import or_
    filters = []
    if card.obj_name:
        filters.append(Deal.obj_name.ilike(card.obj_name))
    if card.title:
        filters.append(Deal.title.ilike(card.title))
    if not filters:
        return None

    query = select(Deal).where(or_(*filters))
    if card.address:
        query = query.where(Deal.address.ilike(card.address))

    result = await db.execute(query)
    return result.scalars().first()


def _build_root_paths(entity_id: str, title: str) -> dict:
    safe_title = clean_name(title or f"Entity {entity_id}")
    base = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    return {
        "tz": f"{base}/[#{entity_id}] {safe_title} (ТЗ)",
        "other": f"{base}/[#{entity_id}] {safe_title} (Прочее)",
        "results": f"{base}/[#{entity_id}] {safe_title} (Результаты)",
    }


@router.get("/executor/cards")
async def get_executor_cards(
    company_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    target_company_ids: List[str] = []
    if company_id:
        target_company_ids.append(str(company_id))
    else:
        link_result = await db.execute(
            select(CompanyUserLink).where(
                CompanyUserLink.user_id == str(user.id),
                CompanyUserLink.link_type.in_(["leader", "employee"]),
            )
        )
        target_company_ids = [str(link.company_id) for link in link_result.scalars().all() if link.company_id]

    if not target_company_ids:
        return []

    query = select(SubcontractorCard).where(_id_in_conditions(SubcontractorCard.company_id, target_company_ids))
    result = await db.execute(query)
    cards = result.scalars().all()
    deduped_cards = list({str(card.id): card for card in cards}.values())

    payload = []
    for card in deduped_cards:
        await _ensure_assignments_for_card(db, card.id)
        assignments_result = await db.execute(
            select(StageProductAssignment).where(_id_conditions(StageProductAssignment.subcontractor_card_id, card.id))
        )
        assignments = assignments_result.scalars().all()
        stage_ids = list({str(item.stage_id) for item in assignments})
        deal_ids = list({str(item.deal_id) for item in assignments})

        stages = []
        if stage_ids:
            stage_uuid_list = []
            for stage_id in stage_ids:
                try:
                    stage_uuid_list.append(uuid.UUID(str(stage_id)))
                except (ValueError, TypeError):
                    continue
            if stage_uuid_list:
                stage_result = await db.execute(select(Stage).where(Stage.id.in_(stage_uuid_list)))
                stages = stage_result.scalars().all()

        deals = []
        if deal_ids:
            deal_filters = []
            for deal_id in deal_ids:
                deal_filters.append(_id_conditions(Deal.id, deal_id))
            deal_result = await db.execute(select(Deal).where(or_(*deal_filters)))
            deals = deal_result.scalars().all()
        deal_lookup = {str(item.id): item for item in deals}

        payload.append(
            {
                "id": card.id,
                "title": card.title,
                "obj_name": card.obj_name,
                "address": card.address,
                "deal_ids": deal_ids,
                "stages": [
                    {
                        "id": str(stage.id),
                        "name": stage.name,
                        "date_start": stage.date_start,
                        "date_end": stage.date_end,
                        "status": stage.status,
                        "deal_id": str(stage.deal_id),
                        "deal_title": deal_lookup.get(str(stage.deal_id)).title if deal_lookup.get(str(stage.deal_id)) else "",
                    }
                    for stage in stages
                ],
            }
        )

    return payload


@router.get("/executor/stages/{stage_id}")
async def get_executor_stage(
    stage_id: str,
    subcontractor_card_id: str,
    db: AsyncSession = Depends(get_db),
):
    stage = await Stage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    card = await SubcontractorCard.get_by_id(db, subcontractor_card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Subcontractor card not found")

    deal = await Deal.get_by_id(db, str(stage.deal_id))
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    await _ensure_assignments_for_card(db, card.id, deal_id=deal.id, stage_id=stage.id)

    deal_products = await DealProduct.get_by_deal(db, deal.id)
    deal_products_map = {_normalize_uuid_like(item.id): item for item in deal_products}
    links = await StageProductLink.get_by_deal(db, str(deal.id))
    links = [link for link in links if _normalize_uuid_like(link.stage_id) == _normalize_uuid_like(stage.id)]

    assignments_result = await db.execute(
        select(StageProductAssignment).where(
            _id_conditions(StageProductAssignment.subcontractor_card_id, subcontractor_card_id),
            _id_conditions(StageProductAssignment.stage_id, stage.id),
        )
    )
    assignments = await _dedupe_assignments(db, assignments_result.scalars().all())
    assignment_ids = [str(item.id) for item in assignments]

    subproduct_lookup = {}
    subproduct_ids = [assignment.subcontractor_product_id for assignment in assignments if assignment.subcontractor_product_id]
    if subproduct_ids:
        subproduct_result = await db.execute(
            select(SubcontractorProduct)
            .options(selectinload(SubcontractorProduct.product))
            .where(or_(*[_id_conditions(SubcontractorProduct.id, sid) for sid in subproduct_ids]))
        )
        subproduct_lookup = {str(item.id): item for item in subproduct_result.scalars().all()}

    stage_deal_products = []
    for link in links:
        deal_product = deal_products_map.get(_normalize_uuid_like(link.deal_product_id))
        if deal_product:
            stage_deal_products.append(deal_product)

    assignments_by_deal_product = {}
    assignments_by_product_key = {}
    for assignment in assignments:
        stage_key = _normalize_uuid_like(assignment.stage_id)
        product_key = _normalize_uuid_like(assignment.product_id)
        matched_deal_product_id = None

        subproduct_name = ""
        if assignment.subcontractor_product_id:
            subproduct = subproduct_lookup.get(str(assignment.subcontractor_product_id))
            if subproduct:
                subproduct_name = _normalize_name(
                    subproduct.custom_name or (subproduct.product.name if subproduct.product else "")
                )

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

    subtasks_map = {}
    if assignment_ids:
        subtasks_result = await db.execute(
            select(StageProductSubtask).where(or_(*[
                _id_conditions(StageProductSubtask.assignment_id, assignment_id)
                for assignment_id in assignment_ids
            ]))
        )
        for subtask in subtasks_result.scalars().all():
            subtasks_map.setdefault(str(subtask.assignment_id), []).append(subtask)

    stage_products = []
    for deal_product in stage_deal_products:
        fallback_key = f"{_normalize_uuid_like(stage.id)}:{_normalize_uuid_like(deal_product.product_id)}"
        matched_assignments = assignments_by_deal_product.get(str(deal_product.id))
        if matched_assignments is None:
            matched_assignments = assignments_by_product_key.get(fallback_key, [])

        for assignment in matched_assignments:
            subproduct = subproduct_lookup.get(str(assignment.subcontractor_product_id))
            if subproduct:
                name = subproduct.custom_name or (subproduct.product.name if subproduct.product else "")
                unit = subproduct.unit
                quantity = subproduct.quantity
                unit_price = subproduct.unit_price
                total_price = subproduct.total_price
                product_id = subproduct.product_id
            else:
                name = deal_product.custom_name or (deal_product.product.name if deal_product.product else "")
                unit = deal_product.unit
                quantity = deal_product.quantity
                unit_price = deal_product.unit_price
                total_price = deal_product.total_price
                product_id = deal_product.product_id

            stage_products.append(
                {
                    "id": assignment.id,
                    "product_id": product_id,
                    "name": name,
                    "unit": unit,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "status": assignment.status,
                    "start_date": assignment.start_date,
                    "due_date": assignment.due_date,
                    "subtasks": [
                        {
                            "id": subtask.id,
                            "title": subtask.title,
                            "due_date": subtask.due_date,
                            "status": subtask.status,
                        }
                        for subtask in subtasks_map.get(str(assignment.id), [])
                    ],
                }
            )

    root_paths = _build_root_paths(deal.id, deal.title)

    return {
        "stage": {
            "id": str(stage.id),
            "name": stage.name,
            "description": stage.description,
            "date_start": stage.date_start,
            "date_end": stage.date_end,
            "status": stage.status,
        },
        "card": {
            "id": card.id,
            "title": card.title,
            "obj_name": card.obj_name,
            "address": card.address,
        },
        "deal": {
            "id": deal.id,
            "title": deal.title,
            "obj_name": deal.obj_name,
            "address": deal.address,
        } if deal else None,
        "products": stage_products,
        "folders": root_paths,
    }


@router.get("/executor/results")
async def get_stage_results(
    stage_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    results = await StageResult.get_by_stage(db, stage_id)
    return results


@router.get("/executor/storage/list")
async def list_storage_items(
    path: str = Query(...),
):
    if not path:
        return []
    try:
        return await list_items(path)
    except Exception:
        return []


@router.post("/executor/storage/create-folder")
async def create_storage_folder(
    path: str = Form(...),
    name: str = Form(...),
):
    folder_path = f"{path.rstrip('/')}/{clean_name(name)}"
    await ensure_path(folder_path)
    return {"path": folder_path}


@router.post("/executor/storage/publish")
async def publish_storage_path(
    path: str = Form(...),
):
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    url = await publish(path)
    return {"url": url}


@router.get("/executor/storage/download")
async def download_storage_item(
    path: str = Query(...),
):
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    href = await get_download_href(path)
    return {"href": href}


@router.post("/executor/storage/upload")
async def upload_storage_files(
    path: str = Form(...),
    files: List[UploadFile] = File(...),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    if not files:
        raise HTTPException(status_code=400, detail="Files are required")

    await ensure_path(path)
    uploaded = 0
    for upload in files:
        content = await upload.read()
        file_path = f"{path.rstrip('/')}/{clean_name(upload.filename)}"
        await upload_bytes_with_safe_extension(file_path, content)
        uploaded += 1

    return {"uploaded": uploaded}


@router.delete("/executor/storage/delete")
async def delete_storage_item(
    path: str = Query(...),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    await delete_path(path)
    return {"deleted": True}


@router.post("/executor/results/upload")
async def upload_stage_results(
    stage_id: str = Form(...),
    product_name: str = Form(...),
    subcontractor_card_id: str = Form(...),
    deal_id: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    if not files:
        raise HTTPException(status_code=400, detail="Files are required")

    card = await SubcontractorCard.get_by_id(db, subcontractor_card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Subcontractor card not found")

    deal = None
    if deal_id:
        deal = await Deal.get_by_id(db, deal_id)
    if not deal:
        deal = await _find_matching_deal(db, card)

    title_source = deal.title if deal else card.title
    root_paths = _build_root_paths(deal.id if deal else card.id, title_source)
    results_root = root_paths["results"]

    product_folder = f"{results_root}/{clean_name(product_name)}"
    await ensure_path(product_folder)

    existing = await list_items(product_folder)
    versions = [
        item["name"]
        for item in existing
        if item["type"] == "folder" and item["name"].lower().startswith("версия ")
    ]
    next_index = 1
    for name in versions:
        try:
            index = int(name.split(" ", 1)[1])
            next_index = max(next_index, index + 1)
        except (IndexError, ValueError):
            continue

    version_label = f"Версия {next_index}"
    version_path = f"{product_folder}/{version_label}"
    await ensure_path(version_path)

    for upload in files:
        content = await upload.read()
        file_path = f"{version_path}/{clean_name(upload.filename)}"
        await upload_bytes_with_safe_extension(file_path, content)

    public_url = await publish(version_path)

    result = await StageResult.create(
        db,
        stage_id=stage_id,
        subcontractor_card_id=subcontractor_card_id,
        deal_id=deal.id if deal else None,
        product_name=product_name,
        version_label=version_label,
        version_number=next_index,
        comment=comment,
        storage_path=version_path,
        public_url=public_url,
        created_by=created_by,
        status="review",
        updated_at=datetime.now(),
    )

    return result


@router.delete("/executor/results/{result_id}")
async def withdraw_stage_result(
    result_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await StageResult.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    if (result.status or "review") != "review":
        raise HTTPException(status_code=400, detail="Можно отозвать только результат на рассмотрении")
    success = await StageResult.delete(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"message": "Result deleted"}
