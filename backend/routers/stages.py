"""
Stages (Этапы работ) API Router - Gantt Chart Management
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Stage, DealProduct, Deal, StageProductLink, IncomeExpenseEntry, Contract, StageDependency, StageProductAssignment, User
from app.models.stage_dependency import normalize_dependency_type
from app.schemas.stage import StageCreate, StageUpdate, StageResponse
from app.services.data_health import safe_refresh_deal_health_issues
from app.services.event_log import log_event
from app.services.gantt_service import GanttService

router = APIRouter()


class StageCopyPayload(BaseModel):
    name: Optional[str] = None
    copy_products: bool = True
    copy_assignments: bool = True


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


def _uuid_string_variants(value):
    normalized = _normalize_uuid_like(value)
    if not normalized:
        return []
    variants = [normalized]
    try:
        parsed = uuid.UUID(normalized)
        variants.extend([str(parsed), parsed.hex])
    except ValueError:
        variants.append(str(value))
    result = []
    for item in variants:
        value_str = str(item)
        if value_str and value_str not in result:
            result.append(value_str)
    return result


def _string_id_conditions(column, value):
    variants = _uuid_string_variants(value)
    if not variants:
        return column == ""
    return or_(*[column == item for item in variants])


def _effective_stage_end(stage: Stage):
    if getattr(stage, "close_date", None) and (
        bool(getattr(stage, "is_closed", False)) or getattr(stage, "status", None) == "completed"
    ):
        return stage.close_date
    return getattr(stage, "date_end", None) or getattr(stage, "date_start", None)


def _stage_snapshot(stage: Optional[Stage]):
    if not stage:
        return {}
    return {
        "name": stage.name,
        "date_start": stage.date_start.isoformat() if getattr(stage, "date_start", None) else None,
        "date_end": stage.date_end.isoformat() if getattr(stage, "date_end", None) else None,
        "close_date": stage.close_date.isoformat() if getattr(stage, "close_date", None) else None,
        "status": stage.status,
        "is_closed": bool(getattr(stage, "is_closed", False)),
        "planned_cost": float(stage.planned_cost or 0),
        "duration": int(stage.duration or 0),
        "term_type": stage.term_type,
        "parent_id": str(stage.parent_id) if getattr(stage, "parent_id", None) else None,
    }


def _stage_changes(before: dict, after: dict):
    changes = {}
    for key in set(before.keys()) | set(after.keys()):
        if before.get(key) != after.get(key):
            changes[key] = {"before": before.get(key), "after": after.get(key)}
    return changes


async def _resolve_deal_contract_id(db: AsyncSession, deal_id: str):
    from sqlalchemy import select, cast, String, or_

    normalized = _normalize_uuid_like(deal_id)
    if not normalized:
        return None
    try:
        deal_uuid = uuid.UUID(normalized)
    except ValueError:
        return None

    query = (
        select(Contract)
        .where(
            or_(
                Contract.deal_id == deal_uuid,
                cast(Contract.deal_id, String) == normalized,
                cast(Contract.deal_id, String) == deal_uuid.hex,
            )
        )
        .order_by(Contract.contract_date.desc())
    )
    contracts = (await db.execute(query)).scalars().all()
    if not contracts:
        return None
    generals = [item for item in contracts if item.contract_type == "general_contractor"]
    if generals:
        return str(generals[0].id)
    if len(contracts) == 1:
        return str(contracts[0].id)
    return None


async def _sync_stage_income_entry(stage: Stage, db: AsyncSession):
    from sqlalchemy import select

    if stage.stage_type != "payment":
        return None

    stage_id = str(stage.id)
    result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.stage_id == stage_id))
    entry = result.scalar_one_or_none()

    amount = float(stage.planned_cost or 0)
    plan_date = stage.date_end or stage.date_start
    normalized_deal_id = _normalize_uuid_like(stage.deal_id)
    deal = await Deal.get_by_id(db, normalized_deal_id or str(stage.deal_id))
    payer_id = _normalize_uuid_like(getattr(deal, "customer_id", None)) if deal else None
    payee_id = _normalize_uuid_like(getattr(deal, "our_company_id", None)) if deal else None
    contract_id = await _resolve_deal_contract_id(db, normalized_deal_id or str(stage.deal_id))

    if entry:
        entry.direction = "income"
        entry.amount = amount
        entry.plan_date = plan_date
        entry.deal_id = normalized_deal_id
        entry.contract_id = contract_id
        entry.payer_id = payer_id
        entry.payee_id = payee_id
        await db.commit()
        return entry

    if amount <= 0:
        return None

    new_entry = IncomeExpenseEntry(
        direction="income",
        payer_id=payer_id,
        payee_id=payee_id,
        deal_id=normalized_deal_id,
        contract_id=contract_id,
        stage_id=stage_id,
        amount=amount,
        plan_date=plan_date
    )
    db.add(new_entry)
    await db.commit()
    return new_entry


async def _would_create_stage_cycle(db: AsyncSession, stage_id: str, predecessor_id: str) -> bool:
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
        if current_id in visited:
            continue
        if current_id == target_id:
            return True
        visited.add(current_id)

        result = await db.execute(
            select(StageDependency.predecessor_id).where(StageDependency.successor_id == current_id)
        )
        for row in result.all():
            predecessor_value = row[0]
            if predecessor_value and predecessor_value not in visited:
                frontier.append(predecessor_value)

    return False

@router.get("/", response_model=List[StageResponse])
async def get_stages(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех этапов"""
    try:
        stages = await Stage.get_all(db, skip=skip, limit=limit)
        return stages
    except Exception as e:
        print(f"Error getting stages: {e}")
        return []

@router.get("/deal/{deal_id}", response_model=List[StageResponse])
async def get_stages_by_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить все этапы проекта"""
    try:
        stages = await Stage.get_by_deal_id(db, deal_id)
        return stages
    except Exception as e:
        print(f"Error getting stages for deal {deal_id}: {e}")
        return []

@router.get("/deal/{deal_id}/products")
async def get_stage_products_by_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get stage-product links for deal."""
    bind = db.get_bind()
    is_sqlite = bool(bind and bind.dialect.name == "sqlite")

    def normalize_stage_id(value):
        if not is_sqlite:
            return str(value)
        try:
            return uuid.UUID(str(value)).hex
        except (ValueError, TypeError):
            return str(value)

    links = await StageProductLink.get_by_deal(db, deal_id)
    return [
        {
            "stage_id": normalize_stage_id(link.stage_id),
            "deal_product_id": str(link.deal_product_id),
        }
        for link in links
    ]


@router.get("/deal/{deal_id}/dependencies")
async def get_stage_dependencies_by_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get stage dependencies for deal."""
    from sqlalchemy import select

    stages = await Stage.get_by_deal_id(db, deal_id)
    stage_ids = [stage.id for stage in stages if getattr(stage, "id", None)]
    if not stage_ids:
        return []

    result = await db.execute(
        select(StageDependency).where(StageDependency.successor_id.in_(stage_ids))
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

@router.put("/{stage_id}/products")
async def set_stage_products(
    stage_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Replace products assigned to stage."""
    stage = await Stage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    deal = await Deal.get_by_id(db, str(stage.deal_id))
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal_product_ids = payload.get("deal_product_ids") or []

    # Validate deal products belong to deal
    valid_products = await DealProduct.get_by_deal(db, str(deal.id))
    valid_ids = {str(item.id) for item in valid_products}
    invalid = [pid for pid in deal_product_ids if str(pid) not in valid_ids]
    if invalid:
        raise HTTPException(status_code=400, detail="Invalid deal products for stage")

    await StageProductLink.delete_by_stage(db, stage_id)
    for deal_product_id in deal_product_ids:
        await StageProductLink.create(
            db,
            deal_id=str(deal.id),
            stage_id=str(stage.id),
            deal_product_id=str(deal_product_id),
        )
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(deal.id),
            action="stage.products",
            created_by=str(user.id),
            details={
                "deal_id": str(deal.id),
                "stage_id": str(stage.id),
                "stage_name": stage.name,
                "products_count": len(deal_product_ids),
                "deal_product_ids": [str(item_id) for item_id in deal_product_ids],
            },
        )
    except Exception:
        pass
    await safe_refresh_deal_health_issues(db, deal.id)
    return {"stage_id": str(stage.id), "deal_product_ids": deal_product_ids}


@router.put("/{stage_id}/dependency")
async def set_stage_dependency(
    stage_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Replace stage predecessor dependencies."""
    from sqlalchemy import delete

    stage = await Stage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    dependency_items = []
    raw_dependencies = payload.get("dependencies")

    if isinstance(raw_dependencies, list):
        seen_predecessors = set()
        for raw_item in raw_dependencies:
            if not isinstance(raw_item, dict):
                continue
            predecessor_id = _normalize_uuid_like(raw_item.get("predecessor_id"))
            if not predecessor_id or predecessor_id in seen_predecessors:
                continue
            dependency_type = normalize_dependency_type(raw_item.get("dependency_type"))
            dependency_items.append({
                "predecessor_id": predecessor_id,
                "dependency_type": dependency_type,
                "lag": int(raw_item.get("lag") or 0),
            })
            seen_predecessors.add(predecessor_id)
    else:
        predecessor_id = _normalize_uuid_like(payload.get("predecessor_id"))
        dependency_type = normalize_dependency_type(payload.get("dependency_type"))
        if predecessor_id:
            dependency_items.append({
                "predecessor_id": predecessor_id,
                "dependency_type": dependency_type,
                "lag": int(payload.get("lag") or 0),
            })

    if not dependency_items:
        await db.execute(delete(StageDependency).where(StageDependency.successor_id == stage.id))
        await db.commit()
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(stage.deal_id),
                action="stage.dependency",
                created_by=str(user.id),
                details={
                    "deal_id": str(stage.deal_id),
                    "stage_id": str(stage.id),
                    "stage_name": stage.name,
                    "predecessor_names": [],
                },
            )
        except Exception:
            pass
        await safe_refresh_deal_health_issues(db, stage.deal_id)
        return {
            "stage_id": str(stage.id),
            "predecessor_id": None,
            "dependency_type": None,
            "lag": 0,
            "dependencies": [],
        }

    predecessors = []
    for item in dependency_items:
        predecessor = await Stage.get_by_id(db, item["predecessor_id"])
        if not predecessor:
            raise HTTPException(status_code=404, detail="Predecessor stage not found")
        if _normalize_uuid_like(predecessor.id) == _normalize_uuid_like(stage.id):
            raise HTTPException(status_code=400, detail="Stage cannot depend on itself")
        if _normalize_uuid_like(predecessor.deal_id) != _normalize_uuid_like(stage.deal_id):
            raise HTTPException(status_code=400, detail="Predecessor stage must belong to the same deal")
        if await _would_create_stage_cycle(db, str(stage.id), str(predecessor.id)):
            raise HTTPException(status_code=400, detail="Dependency cycle is not allowed")
        predecessors.append(predecessor)

    await db.execute(delete(StageDependency).where(StageDependency.successor_id == stage.id))
    created_dependencies = []
    for item, predecessor in zip(dependency_items, predecessors):
        dependency = StageDependency(
            predecessor_id=predecessor.id,
            successor_id=stage.id,
            dependency_type=item["dependency_type"],
            lag=item["lag"],
        )
        db.add(dependency)
        created_dependencies.append(dependency)

    await db.flush()

    resolved_schedule = await GanttService._resolve_successor_schedule(stage, db)
    if resolved_schedule:
        resolved_start, _ = resolved_schedule
        await GanttService.propagate_dates(stage.id, resolved_start, stage.duration, db)
    else:
        await db.commit()

    primary_dependency = created_dependencies[0]
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(stage.deal_id),
            action="stage.dependency",
            created_by=str(user.id),
            details={
                "deal_id": str(stage.deal_id),
                "stage_id": str(stage.id),
                "stage_name": stage.name,
                "predecessor_ids": [str(item.predecessor_id) for item in created_dependencies],
                "predecessor_names": [predecessor.name for predecessor in predecessors],
                "dependencies": [
                    {
                        "predecessor_id": str(item.predecessor_id),
                        "dependency_type": normalize_dependency_type(item.dependency_type),
                        "lag": item.lag,
                    }
                    for item in created_dependencies
                ],
            },
        )
    except Exception:
        pass

    await safe_refresh_deal_health_issues(db, stage.deal_id)
    return {
        "id": str(primary_dependency.id),
        "stage_id": str(stage.id),
        "predecessor_id": str(primary_dependency.predecessor_id) if len(created_dependencies) == 1 else None,
        "dependency_type": normalize_dependency_type(primary_dependency.dependency_type) if len(created_dependencies) == 1 else None,
        "lag": primary_dependency.lag if len(created_dependencies) == 1 else 0,
        "dependencies": [
            {
                "id": str(item.id),
                "predecessor_id": str(item.predecessor_id),
                "successor_id": str(item.successor_id),
                "dependency_type": normalize_dependency_type(item.dependency_type),
                "lag": item.lag,
            }
            for item in created_dependencies
        ],
    }


@router.post("/", response_model=StageResponse)
async def create_stage(
    stage: StageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать новый этап"""
    try:
        stage_data = stage.dict()
        print(f"Creating stage with data: {stage_data}")
        db_stage = await Stage.create(db, **stage_data)
        
        await _sync_stage_income_entry(db_stage, db)
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(db_stage.deal_id),
                action="stage.create",
                created_by=str(user.id),
                details={
                    "deal_id": str(db_stage.deal_id),
                    "stage_id": str(db_stage.id),
                    "stage_name": db_stage.name,
                    "date_start": db_stage.date_start.isoformat() if db_stage.date_start else None,
                    "date_end": db_stage.date_end.isoformat() if db_stage.date_end else None,
                    "stage_type": db_stage.stage_type,
                    "planned_cost": float(db_stage.planned_cost or 0),
                },
            )
        except Exception:
            pass
        await safe_refresh_deal_health_issues(db, db_stage.deal_id)
        return db_stage
    except Exception as e:
        print(f"Error creating stage: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Ошибка создания этапа: {str(e)}")


@router.post("/{stage_id}/copy", response_model=StageResponse)
async def copy_stage(
    stage_id: str,
    payload: Optional[StageCopyPayload] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Create a new editable stage copy in the same deal."""
    from datetime import datetime

    source = await Stage.get_by_id(db, stage_id)
    if not source:
        raise HTTPException(status_code=404, detail="Stage not found")

    payload = payload or StageCopyPayload()
    now = datetime.now()
    copy_name = (payload.name or f"{source.name} (копия)").strip()
    new_stage = Stage(
        parent_id=source.parent_id,
        deal_id=source.deal_id,
        name=copy_name,
        description=source.description,
        stage_type=source.stage_type,
        term_type=source.term_type,
        date_start=source.date_start,
        duration=source.duration,
        date_end=source.date_end,
        close_date=None,
        resources=source.resources or [],
        planned_cost=float(source.planned_cost or 0),
        actual_cost=0.0,
        status="planned",
        is_closed=False,
        subcontractor_id=source.subcontractor_id,
        created_at=now,
        updated_at=now,
    )
    db.add(new_stage)
    await db.flush()

    copied_products = 0
    if payload.copy_products:
        product_links_result = await db.execute(
            select(StageProductLink).where(_string_id_conditions(StageProductLink.stage_id, source.id))
        )
        product_links = product_links_result.scalars().all()
        seen_products = set()
        for link in product_links:
            product_id = str(link.deal_product_id)
            if product_id in seen_products:
                continue
            seen_products.add(product_id)
            db.add(StageProductLink(
                deal_id=str(new_stage.deal_id),
                stage_id=str(new_stage.id),
                deal_product_id=product_id,
            ))
            copied_products += 1

    copied_assignments = 0
    if payload.copy_assignments:
        assignments_result = await db.execute(
            select(StageProductAssignment).where(_string_id_conditions(StageProductAssignment.stage_id, source.id))
        )
        assignments = assignments_result.scalars().all()
        seen_assignments = set()
        for assignment in assignments:
            key = (
                str(assignment.product_id),
                str(assignment.subcontractor_card_id),
                str(assignment.contract_id or ""),
                str(assignment.subcontractor_product_id or ""),
            )
            if key in seen_assignments:
                continue
            seen_assignments.add(key)
            db.add(StageProductAssignment(
                deal_id=str(new_stage.deal_id),
                stage_id=str(new_stage.id),
                product_id=str(assignment.product_id),
                subcontractor_card_id=str(assignment.subcontractor_card_id),
                subcontractor_product_id=str(assignment.subcontractor_product_id) if assignment.subcontractor_product_id else None,
                contract_id=str(assignment.contract_id) if assignment.contract_id else None,
                start_date=assignment.start_date,
                due_date=assignment.due_date,
                contract_due_date=assignment.contract_due_date,
                status="not_started",
                created_at=now,
                updated_at=now,
            ))
            copied_assignments += 1

    await db.commit()
    await db.refresh(new_stage)

    await _sync_stage_income_entry(new_stage, db)
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(new_stage.deal_id),
            action="stage.copy",
            created_by=str(user.id),
            details={
                "deal_id": str(new_stage.deal_id),
                "source_stage_id": str(source.id),
                "source_stage_name": source.name,
                "stage_id": str(new_stage.id),
                "stage_name": new_stage.name,
                "copied_products": copied_products,
                "copied_assignments": copied_assignments,
            },
        )
    except Exception:
        pass

    await safe_refresh_deal_health_issues(db, new_stage.deal_id)
    return new_stage


@router.get("/{stage_id}", response_model=StageResponse)
async def get_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить этап по ID"""
    stage = await Stage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Этап не найден")
    return stage

@router.put("/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: str,
    stage_update: StageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обновить этап"""
    print(f"🔄 UPDATE STAGE CALLED: {stage_id}, data: {stage_update.dict(exclude_unset=True)}")
    try:
        # Get old stage data before update
        old_stage = await Stage.get_by_id(db, stage_id)
        if not old_stage:
            raise HTTPException(status_code=404, detail="Этап не найден")
        
        before_snapshot = _stage_snapshot(old_stage)
        old_start = old_stage.date_start
        old_duration = old_stage.duration
        old_term_type = old_stage.term_type
        old_effective_end = _effective_stage_end(old_stage)

        # Lock stage_type after creation
        update_data = stage_update.dict(exclude_unset=True)
        update_data["stage_type"] = old_stage.stage_type

        # Update stage
        stage = await Stage.update(db, stage_id, **update_data)
        if not stage:
            raise HTTPException(status_code=404, detail="Этап не найден")
        
        schedule_changed = (
            old_start != stage.date_start or
            old_duration != stage.duration or
            old_term_type != stage.term_type
        )
        effective_end_changed = old_effective_end != _effective_stage_end(stage)
        if schedule_changed or effective_end_changed:
            result = await GanttService.propagate_dates(stage.id, stage.date_start, stage.duration, db)
            updated_stage_id = result.get("updated_stage", {}).get("id")
            if updated_stage_id:
                refreshed_stage = await Stage.get_by_id(db, updated_stage_id)
                if refreshed_stage:
                    stage = refreshed_stage

        await _sync_stage_income_entry(stage, db)
        try:
            await log_event(
                db,
                entity_type="deal",
                entity_id=str(stage.deal_id),
                action="stage.update",
                created_by=str(user.id),
                details={
                    "deal_id": str(stage.deal_id),
                    "stage_id": str(stage.id),
                    "stage_name": stage.name,
                    "date_start": stage.date_start.isoformat() if stage.date_start else None,
                    "date_end": stage.date_end.isoformat() if stage.date_end else None,
                    "close_date": stage.close_date.isoformat() if stage.close_date else None,
                    "changes": _stage_changes(before_snapshot, _stage_snapshot(stage)),
                },
            )
        except Exception:
            pass
        await safe_refresh_deal_health_issues(db, stage.deal_id)
        return stage
    except Exception as e:
        print(f"Error updating stage {stage_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Ошибка обновления этапа")

@router.delete("/{stage_id}")
async def delete_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить этап"""
    from sqlalchemy import delete

    # Get stage before deletion to check if it's a payment stage
    stage = await Stage.get_by_id(db, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Этап не найден")
    stage_snapshot = _stage_snapshot(stage)

    # If payment stage, delete related cash flow entries
    if stage.stage_type == "payment":
        from app.models import IncomeExpenseEntry
        # Delete income entry by stage_id (much more reliable!)
        delete_query = delete(IncomeExpenseEntry).where(
            IncomeExpenseEntry.stage_id == str(stage.id)
        )
        result = await db.execute(delete_query)
        await db.commit()
        print(f"✓ Deleted {result.rowcount} cash flow entry for payment stage: {stage.name}")

    # Remove dependency rows where the stage participates as predecessor or successor.
    await db.execute(
        delete(StageDependency).where(
            or_(
                StageDependency.predecessor_id == stage.id,
                StageDependency.successor_id == stage.id,
            )
        )
    )
    await db.commit()
    
    # Delete the stage
    success = await Stage.delete(db, stage_id)
    if not success:
        raise HTTPException(status_code=404, detail="Этап не найден")
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(stage.deal_id),
            action="stage.delete",
            created_by=str(user.id),
            details={
                "deal_id": str(stage.deal_id),
                "stage_id": str(stage.id),
                "stage_name": stage_snapshot.get("name") or stage.name,
                "date_start": stage_snapshot.get("date_start"),
                "date_end": stage_snapshot.get("date_end"),
            },
        )
    except Exception:
        pass
    await safe_refresh_deal_health_issues(db, stage.deal_id)
    return {"message": "Этап удален"}

@router.post("/{stage_id}/propagate")
async def propagate_dates(
    stage_id: str,
    new_start_date: Optional[str] = None,
    new_duration: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Пересчитать даты этапов при изменении параметров"""
    from datetime import datetime
    try:
        # Convert string date to date object if provided
        start_date = None
        if new_start_date:
            start_date = datetime.fromisoformat(new_start_date).date()

        result = await GanttService.propagate_dates(
            stage_id, start_date, new_duration, db
        )
        return result
    except Exception as e:
        print(f"Error propagating dates for stage {stage_id}: {e}")
        raise HTTPException(status_code=400, detail="Ошибка пересчета дат")

@router.get("/gantt/{deal_id}")
async def get_gantt_tree(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить дерево этапов для Gantt диаграммы"""
    try:
        tree = await GanttService.get_gantt_tree(deal_id, db)
        return tree
    except Exception as e:
        print(f"Error getting Gantt tree for deal {deal_id}: {e}")
        raise HTTPException(status_code=400, detail="Ошибка получения дерева Gantt")
