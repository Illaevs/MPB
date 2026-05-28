"""
Subcontractor stages API router
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import (
    SubcontractorStage,
    SubcontractorStageDependency,
    IncomeExpenseEntry,
    SubcontractorCard,
    Contract,
    Deal,
)
from app.models.stage_dependency import normalize_dependency_type
from app.schemas.subcontractor_stage import (
    SubcontractorStageCreate,
    SubcontractorStageUpdate,
    SubcontractorStageResponse
)
from app.services.event_outbox import emit_event_safe
from app.services.subcontractor_gantt_service import SubcontractorGanttService

router = APIRouter()


def _as_str(value):
    return str(value) if value is not None else None


def _normalize_uuid_like(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    hex_only = "".join(ch for ch in raw if ch.lower() in "0123456789abcdef")
    if len(hex_only) == 32:
        try:
            return str(uuid.UUID(hex_only))
        except ValueError:
            pass
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return raw


def _effective_stage_end(stage: SubcontractorStage):
    if getattr(stage, "close_date", None) and getattr(stage, "status", None) == "completed":
        return stage.close_date
    return getattr(stage, "date_end", None) or getattr(stage, "date_start", None)


async def _would_create_sub_stage_cycle(db: AsyncSession, stage_id: str, predecessor_id: str) -> bool:
    from sqlalchemy import select

    normalized_stage_id = _normalize_uuid_like(stage_id)
    normalized_predecessor_id = _normalize_uuid_like(predecessor_id)
    if not normalized_stage_id or not normalized_predecessor_id:
        return False

    target_id = uuid.UUID(normalized_stage_id)
    frontier = [uuid.UUID(normalized_predecessor_id)]
    visited = set()

    while frontier:
        current_id = frontier.pop()
        if current_id == target_id:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)

        result = await db.execute(
            select(SubcontractorStageDependency.predecessor_id)
            .where(SubcontractorStageDependency.successor_id == current_id)
        )
        frontier.extend(
            predecessor
            for predecessor in result.scalars().all()
            if predecessor and predecessor not in visited
        )
    return False


async def _resolve_payment_links(stage: SubcontractorStage, db: AsyncSession):
    card = await SubcontractorCard.get_by_id(db, str(stage.subcontractor_card_id))
    contract = await Contract.get_by_id(db, str(stage.contract_id)) if stage.contract_id else None

    deal_id_value = _as_str(getattr(contract, "deal_id", None)) if contract else None
    payer_company_id = None
    payee_company_id = None

    if card and getattr(card, "company_id", None):
        payee_company_id = _as_str(card.company_id)
    if not payee_company_id and contract and getattr(contract, "executor_id", None):
        payee_company_id = _as_str(contract.executor_id)

    if contract and getattr(contract, "customer_id", None):
        payer_company_id = _as_str(contract.customer_id)
    if not payer_company_id and card and getattr(card, "general_contractor_id", None):
        payer_company_id = _as_str(card.general_contractor_id)
    if not payer_company_id and card and getattr(card, "customer_id", None):
        payer_company_id = _as_str(card.customer_id)

    if deal_id_value:
        deal = await Deal.get_by_id(db, deal_id_value)
        if deal and getattr(deal, "our_company_id", None):
            payer_company_id = _as_str(deal.our_company_id)

    return {
        "deal_id": deal_id_value,
        "contract_id": _as_str(stage.contract_id) if stage.contract_id else None,
        "payer_id": payer_company_id,
        "payee_id": payee_company_id,
    }


async def _sync_payment_entry(stage: SubcontractorStage, db: AsyncSession):
    if stage.stage_type != "payment":
        return None

    from sqlalchemy import select

    query = select(IncomeExpenseEntry).where(IncomeExpenseEntry.stage_id == str(stage.id))
    result = await db.execute(query)
    entry = result.scalar_one_or_none()

    amount = float(stage.planned_cost or 0)
    links = await _resolve_payment_links(stage, db)
    plan_date = stage.date_end or stage.date_start

    if amount <= 0:
        if entry:
            entry.amount = 0
            entry.plan_date = plan_date
            entry.contract_id = links["contract_id"]
            entry.deal_id = links["deal_id"]
            entry.payer_id = links["payer_id"]
            entry.payee_id = links["payee_id"]
            await db.commit()
        return entry

    if entry:
        entry.direction = "expense"
        entry.amount = amount
        entry.plan_date = plan_date
        entry.contract_id = links["contract_id"]
        entry.deal_id = links["deal_id"]
        entry.payer_id = links["payer_id"]
        entry.payee_id = links["payee_id"]
        await db.commit()
        return entry

    entry = IncomeExpenseEntry(
        direction="expense",
        payer_id=links["payer_id"],
        payee_id=links["payee_id"],
        deal_id=links["deal_id"],
        contract_id=links["contract_id"],
        stage_id=str(stage.id),
        amount=amount,
        plan_date=plan_date,
    )
    db.add(entry)
    await db.commit()
    return entry


@router.get("/", response_model=List[SubcontractorStageResponse])
async def get_stages(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    try:
        stages = await SubcontractorStage.get_all(db, skip=skip, limit=limit)
        return stages
    except Exception as e:
        print(f"Error getting subcontractor stages: {e}")
        return []


@router.get("/subcontractor/{subcontractor_id}", response_model=List[SubcontractorStageResponse])
async def get_stages_by_subcontractor(
    subcontractor_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        stages = await SubcontractorStage.get_by_subcontractor_card_id(db, subcontractor_id)
        return stages
    except Exception as e:
        print(f"Error getting stages for subcontractor {subcontractor_id}: {e}")
        return []


@router.get("/subcontractor/{subcontractor_id}/dependencies")
async def get_stage_dependencies_by_subcontractor(
    subcontractor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get subcontractor stage dependencies for subcontractor card."""
    from sqlalchemy import select

    stages = await SubcontractorStage.get_by_subcontractor_card_id(db, subcontractor_id)
    stage_ids = [stage.id for stage in stages if getattr(stage, "id", None)]
    if not stage_ids:
        return []

    result = await db.execute(
        select(SubcontractorStageDependency).where(SubcontractorStageDependency.successor_id.in_(stage_ids))
    )
    dependencies = result.scalars().all()
    return [
        {
            "id": str(dep.id),
            "predecessor_id": str(dep.predecessor_id),
            "successor_id": str(dep.successor_id),
            "dependency_type": normalize_dependency_type(dep.dependency_type),
            "lag": dep.lag,
        }
        for dep in dependencies
    ]


@router.post("/", response_model=SubcontractorStageResponse)
async def create_stage(
    stage: SubcontractorStageCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        stage_data = stage.dict()
        db_stage = await SubcontractorStage.create(db, **stage_data)

        # Keep DDS in sync for payment stages.
        await _sync_payment_entry(db_stage, db)

        await emit_event_safe(
            db,
            event_type="subcontractor_stage.after_create",
            entity_type="subcontractor_stage",
            entity_id=str(db_stage.id),
            payload={
                "id": str(db_stage.id),
                "card_id": str(getattr(db_stage, "card_id", None)) if getattr(db_stage, "card_id", None) else None,
                "name": getattr(db_stage, "name", None),
                "stage_type": getattr(db_stage, "stage_type", None),
                "status": getattr(db_stage, "status", None),
            },
            payload_version=1,
        )
        return db_stage
    except Exception as e:
        print(f"Error creating subcontractor stage: {e}")
        raise HTTPException(status_code=400, detail=f"???????????? ???????????????? ??????????: {str(e)}")


@router.get("/{stage_id}", response_model=SubcontractorStageResponse)
async def get_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db)
):
    stage = await SubcontractorStage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Этап не найден")
    return stage


@router.put("/{stage_id}", response_model=SubcontractorStageResponse)
async def update_stage(
    stage_id: str,
    stage_update: SubcontractorStageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update subcontractor stage"""
    try:
        # Get old stage data
        old_stage = await SubcontractorStage.get_by_id(db, stage_id)
        if not old_stage:
            raise HTTPException(status_code=404, detail="Stage not found")
        old_start = old_stage.date_start
        old_duration = old_stage.duration
        old_term_type = old_stage.term_type
        old_effective_end = _effective_stage_end(old_stage)
        old_status = getattr(old_stage, "status", None)

        # Lock stage_type after creation
        update_data = stage_update.dict(exclude_unset=True)
        update_data["stage_type"] = old_stage.stage_type

        # Update stage
        stage = await SubcontractorStage.update(db, stage_id, **update_data)
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")
        schedule_changed = (
            old_start != stage.date_start or
            old_duration != stage.duration or
            old_term_type != stage.term_type
        )
        effective_end_changed = old_effective_end != _effective_stage_end(stage)
        if schedule_changed or effective_end_changed:
            result = await SubcontractorGanttService.propagate_dates(stage.id, stage.date_start, stage.duration, db)
            updated_stage_id = result.get("updated_stage", {}).get("id")
            if updated_stage_id:
                refreshed_stage = await SubcontractorStage.get_by_id(db, updated_stage_id)
                if refreshed_stage:
                    stage = refreshed_stage

        # Sync cash flow entry if payment stage.
        await _sync_payment_entry(stage, db)
        new_status = getattr(stage, "status", None)
        if old_status != new_status:
            await emit_event_safe(
                db,
                event_type="subcontractor_stage.after_status_change",
                entity_type="subcontractor_stage",
                entity_id=str(stage.id),
                payload={
                    "id": str(stage.id),
                    "card_id": str(getattr(stage, "card_id", None)) if getattr(stage, "card_id", None) else None,
                    "name": getattr(stage, "name", None),
                    "status_before": old_status,
                    "status_after": new_status,
                },
                payload_version=1,
            )
        return stage
    except Exception as e:
        print(f"Error updating subcontractor stage {stage_id}: {e}")
        raise HTTPException(status_code=400, detail="Error updating stage")


@router.put("/{stage_id}/dependency")
async def set_stage_dependency(
    stage_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Set a single predecessor dependency for subcontractor stage."""
    from sqlalchemy import delete

    stage = await SubcontractorStage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    predecessor_id = _normalize_uuid_like(payload.get("predecessor_id"))
    dependency_type = normalize_dependency_type(payload.get("dependency_type"))
    lag = int(payload.get("lag") or 0)

    if not predecessor_id:
        await db.execute(delete(SubcontractorStageDependency).where(SubcontractorStageDependency.successor_id == stage.id))
        await db.commit()
        return {
            "stage_id": str(stage.id),
            "predecessor_id": None,
            "dependency_type": None,
            "lag": 0,
        }

    predecessor = await SubcontractorStage.get_by_id(db, predecessor_id)
    if not predecessor:
        raise HTTPException(status_code=404, detail="Predecessor stage not found")
    if _normalize_uuid_like(predecessor.id) == _normalize_uuid_like(stage.id):
        raise HTTPException(status_code=400, detail="Stage cannot depend on itself")
    if _normalize_uuid_like(predecessor.subcontractor_card_id) != _normalize_uuid_like(stage.subcontractor_card_id):
        raise HTTPException(status_code=400, detail="Predecessor stage must belong to the same subcontractor")
    if _normalize_uuid_like(predecessor.contract_id) != _normalize_uuid_like(stage.contract_id):
        raise HTTPException(status_code=400, detail="Predecessor stage must belong to the same contract")
    if await _would_create_sub_stage_cycle(db, str(stage.id), str(predecessor.id)):
        raise HTTPException(status_code=400, detail="Dependency cycle is not allowed")

    await db.execute(delete(SubcontractorStageDependency).where(SubcontractorStageDependency.successor_id == stage.id))
    dependency = SubcontractorStageDependency(
        predecessor_id=predecessor.id,
        successor_id=stage.id,
        dependency_type=dependency_type,
        lag=lag,
    )
    db.add(dependency)
    await db.commit()

    result = await SubcontractorGanttService.propagate_dates(predecessor.id, None, None, db)
    updated_stage_id = result.get("updated_stage", {}).get("id")
    if updated_stage_id:
        refreshed_stage = await SubcontractorStage.get_by_id(db, updated_stage_id)
        if refreshed_stage:
            stage = refreshed_stage

    return {
        "stage_id": str(stage.id),
        "predecessor_id": str(predecessor.id),
        "dependency_type": dependency_type,
        "lag": lag,
    }


@router.delete("/{stage_id}")
async def delete_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete subcontractor stage"""
    from sqlalchemy import delete, or_

    # Get stage before deletion
    stage = await SubcontractorStage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    # If payment stage, delete related expense entry
    if stage.stage_type == "payment":
        from app.models import IncomeExpenseEntry
        from sqlalchemy import delete
        
        # Delete expense entry by stage_id
        delete_query = delete(IncomeExpenseEntry).where(
            IncomeExpenseEntry.stage_id == str(stage.id)
        )
        result = await db.execute(delete_query)
        await db.commit()
        print(f"Deleted {result.rowcount} expense entry for subcontractor payment stage: {stage.name}")

    # Clear product links for this stage
    from app.models import SubcontractorProduct
    from sqlalchemy import update as sqlalchemy_update

    reset_query = sqlalchemy_update(SubcontractorProduct).where(
        SubcontractorProduct.stage_id == str(stage.id)
    ).values(stage_id=None)
    result = await db.execute(reset_query)
    await db.commit()
    print(f"Cleared {result.rowcount} products stage link for stage: {stage.name}")

    await db.execute(
        delete(SubcontractorStageDependency).where(
            or_(
                SubcontractorStageDependency.predecessor_id == stage.id,
                SubcontractorStageDependency.successor_id == stage.id,
            )
        )
    )
    await db.commit()
    
    # Delete the stage
    success = await SubcontractorStage.delete(db, stage_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stage not found")
    return {"message": "Stage deleted"}


@router.post("/{stage_id}/propagate")
async def propagate_dates(
    stage_id: str,
    new_start_date: Optional[str] = None,
    new_duration: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    try:
        start_date = None
        if new_start_date:
            start_date = datetime.fromisoformat(new_start_date).date()

        result = await SubcontractorGanttService.propagate_dates(
            stage_id, start_date, new_duration, db
        )
        return result
    except Exception as e:
        print(f"Error propagating dates for subcontractor stage {stage_id}: {e}")
        raise HTTPException(status_code=400, detail="Ошибка перерасчета дат")


@router.get("/gantt/{subcontractor_id}")
async def get_gantt_tree(
    subcontractor_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        tree = await SubcontractorGanttService.get_gantt_tree(subcontractor_id, db)
        return tree
    except Exception as e:
        print(f"Error getting gantt tree for subcontractor {subcontractor_id}: {e}")
        raise HTTPException(status_code=400, detail="Ошибка загрузки дерева Gantt")
