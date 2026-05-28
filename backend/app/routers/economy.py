import re
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import (
    InflationIndex,
    Overhead,
    OverheadAllocation,
    WipMonthly,
    AdvancePayment,
    StageClosing,
    PricingModel,
    PricingQuote,
    QualityAlert,
)
from app.schemas.inflation_index import (
    InflationIndexCreate,
    InflationIndexUpdate,
    InflationIndexResponse,
)
from app.schemas.overhead import OverheadCreate, OverheadUpdate, OverheadResponse
from app.schemas.overhead_allocation import OverheadAllocationResponse
from app.schemas.wip_monthly import WipMonthlyResponse
from app.schemas.advance_payment import (
    AdvancePaymentCreate,
    AdvancePaymentUpdate,
    AdvancePaymentResponse,
)
from app.schemas.stage_closing import StageClosingCreate, StageClosingResponse
from app.schemas.pricing_model import (
    PricingModelCreate,
    PricingModelUpdate,
    PricingModelResponse,
)
from app.schemas.pricing_quote import PricingQuoteCreate, PricingQuoteResponse
from app.schemas.quality_alert import QualityAlertCreate, QualityAlertResponse
from app.services.economy_service import EconomyService

router = APIRouter()


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        raw = str(value)
        if re.fullmatch(r"[0-9a-fA-F]{32}", raw):
            raw = f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
        return value if isinstance(value, uuid.UUID) else uuid.UUID(raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


@router.get("/wip", response_model=List[WipMonthlyResponse])
async def list_wip(
    deal_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(WipMonthly).order_by(WipMonthly.period)
    if deal_id:
        query = query.where(WipMonthly.deal_id == _parse_uuid(deal_id, "deal_id"))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/wip/rebuild", response_model=List[WipMonthlyResponse])
async def rebuild_wip(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
):
    deal_uuid = _parse_uuid(deal_id, "deal_id")
    return await EconomyService.rebuild_wip_for_deal(deal_uuid, db)


@router.get("/inflation", response_model=List[InflationIndexResponse])
async def list_inflation(db: AsyncSession = Depends(get_db)):
    return await InflationIndex.get_all(db)


@router.post("/inflation", response_model=InflationIndexResponse)
async def create_inflation(
    payload: InflationIndexCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await InflationIndex.get_by_period(db, payload.period)
    if existing:
        raise HTTPException(status_code=400, detail="Period already exists")
    return await InflationIndex.create(db, **payload.dict())


@router.put("/inflation/{item_id}", response_model=InflationIndexResponse)
async def update_inflation(
    item_id: str,
    payload: InflationIndexUpdate,
    db: AsyncSession = Depends(get_db),
):
    item = await InflationIndex.get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inflation index not found")
    return await InflationIndex.update(db, item_id, **payload.dict(exclude_unset=True))


@router.delete("/inflation/{item_id}")
async def delete_inflation(item_id: str, db: AsyncSession = Depends(get_db)):
    success = await InflationIndex.delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inflation index not found")
    return {"message": "Deleted"}


@router.get("/overheads", response_model=List[OverheadResponse])
async def list_overheads(db: AsyncSession = Depends(get_db)):
    return await Overhead.get_all(db)


@router.post("/overheads", response_model=OverheadResponse)
async def create_overhead(
    payload: OverheadCreate,
    db: AsyncSession = Depends(get_db),
):
    return await Overhead.create(db, **payload.dict())


@router.put("/overheads/{item_id}", response_model=OverheadResponse)
async def update_overhead(
    item_id: str,
    payload: OverheadUpdate,
    db: AsyncSession = Depends(get_db),
):
    item = await Overhead.get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Overhead not found")
    return await Overhead.update(db, item_id, **payload.dict(exclude_unset=True))


@router.delete("/overheads/{item_id}")
async def delete_overhead(item_id: str, db: AsyncSession = Depends(get_db)):
    success = await Overhead.delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Overhead not found")
    return {"message": "Deleted"}


@router.post("/overheads/allocate", response_model=List[OverheadAllocationResponse])
async def allocate_overheads(
    period: str,
    db: AsyncSession = Depends(get_db),
):
    return await EconomyService.allocate_overheads(period, db)


@router.post("/overheads/import-dds", response_model=List[OverheadResponse])
async def import_overheads_from_dds(
    db: AsyncSession = Depends(get_db),
):
    excluded_prefixes = ["2.3.1", "2.3.2"]
    return await EconomyService.import_overheads_from_dds(db, excluded_prefixes=excluded_prefixes)


@router.get("/overheads/allocations", response_model=List[OverheadAllocationResponse])
async def list_overhead_allocations(
    deal_id: Optional[str] = None,
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(OverheadAllocation)
    if deal_id:
        query = query.where(OverheadAllocation.deal_id == _parse_uuid(deal_id, "deal_id"))
    if period:
        query = query.where(OverheadAllocation.period == period)
    result = await db.execute(query.order_by(OverheadAllocation.period))
    return result.scalars().all()


@router.get("/advances", response_model=List[AdvancePaymentResponse])
async def list_advances(
    deal_id: Optional[str] = None,
    contract_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AdvancePayment)
    if deal_id:
        query = query.where(AdvancePayment.deal_id == _parse_uuid(deal_id, "deal_id"))
    if contract_id:
        query = query.where(AdvancePayment.contract_id == _parse_uuid(contract_id, "contract_id"))
    result = await db.execute(query.order_by(AdvancePayment.created_at.desc()))
    return result.scalars().all()


@router.post("/advances", response_model=AdvancePaymentResponse)
async def create_advance(
    payload: AdvancePaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    data = payload.dict()
    if not data.get("remaining_total"):
        data["remaining_total"] = data.get("amount_total", 0.0)
    item = AdvancePayment(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/advances/{item_id}", response_model=AdvancePaymentResponse)
async def update_advance(
    item_id: str,
    payload: AdvancePaymentUpdate,
    db: AsyncSession = Depends(get_db),
):
    item_uuid = _parse_uuid(item_id, "advance_id")
    result = await db.execute(select(AdvancePayment).where(AdvancePayment.id == item_uuid))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Advance not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/stage-closings", response_model=StageClosingResponse)
async def create_stage_closing(
    payload: StageClosingCreate,
    db: AsyncSession = Depends(get_db),
):
    advance_query = select(AdvancePayment).where(AdvancePayment.remaining_total > 0)
    if payload.contract_id:
        advance_query = advance_query.where(AdvancePayment.contract_id == payload.contract_id)
    elif payload.deal_id:
        advance_query = advance_query.where(AdvancePayment.deal_id == payload.deal_id)

    advance_result = await db.execute(advance_query.order_by(AdvancePayment.created_at))
    advance = advance_result.scalars().first()

    base_amount = payload.base_amount
    advance_covered_base = 0.0
    advance_covered_vat = 0.0
    remaining_base = base_amount

    if advance:
        advance_base = advance.remaining_total / (1 + advance.vat_rate / 100.0)
        advance_covered_base = min(base_amount, advance_base)
        advance_covered_vat = advance_covered_base * advance.vat_rate / 100.0
        remaining_base = base_amount - advance_covered_base
        advance.remaining_total = max(
            advance.remaining_total - advance_covered_base * (1 + advance.vat_rate / 100.0),
            0.0,
        )

    vat_rate = EconomyService.vat_rate_for_date(payload.closing_date)
    remaining_vat = remaining_base * vat_rate / 100.0
    total_vat = advance_covered_vat + remaining_vat
    total_amount = base_amount + total_vat

    closing = StageClosing(
        stage_id=payload.stage_id,
        deal_id=payload.deal_id,
        contract_id=payload.contract_id,
        closing_date=payload.closing_date,
        base_amount=base_amount,
        vat_rate=vat_rate,
        vat_amount=total_vat,
        total_amount=total_amount,
        advance_covered_base=advance_covered_base,
        advance_covered_vat=advance_covered_vat,
        remaining_base=remaining_base,
        remaining_vat=remaining_vat,
    )
    db.add(closing)
    await db.commit()
    await db.refresh(closing)
    return closing


@router.get("/stage-closings", response_model=List[StageClosingResponse])
async def list_stage_closings(
    deal_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(StageClosing)
    if deal_id:
        query = query.where(StageClosing.deal_id == _parse_uuid(deal_id, "deal_id"))
    if stage_id:
        query = query.where(StageClosing.stage_id == _parse_uuid(stage_id, "stage_id"))
    result = await db.execute(query.order_by(StageClosing.closing_date))
    return result.scalars().all()


@router.get("/pricing/models", response_model=List[PricingModelResponse])
async def list_pricing_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PricingModel).order_by(PricingModel.created_at.desc()))
    return result.scalars().all()


@router.post("/pricing/models", response_model=PricingModelResponse)
async def create_pricing_model(
    payload: PricingModelCreate,
    db: AsyncSession = Depends(get_db),
):
    model = PricingModel(**payload.dict())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.put("/pricing/models/{item_id}", response_model=PricingModelResponse)
async def update_pricing_model(
    item_id: str,
    payload: PricingModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    item_uuid = _parse_uuid(item_id, "model_id")
    result = await db.execute(select(PricingModel).where(PricingModel.id == item_uuid))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Pricing model not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(model, key, value)
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/pricing/models/{item_id}")
async def delete_pricing_model(item_id: str, db: AsyncSession = Depends(get_db)):
    item_uuid = _parse_uuid(item_id, "model_id")
    result = await db.execute(select(PricingModel).where(PricingModel.id == item_uuid))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Pricing model not found")
    await db.delete(model)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/pricing/quote", response_model=PricingQuoteResponse)
async def create_pricing_quote(
    payload: PricingQuoteCreate,
    db: AsyncSession = Depends(get_db),
):
    quote = await EconomyService.calculate_pricing_quote(
        deal_id=payload.deal_id,
        model_id=payload.model_id,
        db=db,
        margin=payload.margin,
        risk=payload.risk,
        calc_date=payload.calc_date,
    )
    return quote


@router.get("/pricing/quotes", response_model=List[PricingQuoteResponse])
async def list_pricing_quotes(
    deal_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PricingQuote)
    if deal_id:
        query = query.where(PricingQuote.deal_id == _parse_uuid(deal_id, "deal_id"))
    result = await db.execute(query.order_by(PricingQuote.calc_date.desc()))
    return result.scalars().all()


@router.get("/alerts", response_model=List[QualityAlertResponse])
async def list_quality_alerts(
    deal_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(QualityAlert)
    if deal_id:
        query = query.where(QualityAlert.deal_id == _parse_uuid(deal_id, "deal_id"))
    result = await db.execute(query.order_by(QualityAlert.created_at.desc()))
    return result.scalars().all()


@router.post("/alerts", response_model=QualityAlertResponse)
async def create_quality_alert(
    payload: QualityAlertCreate,
    db: AsyncSession = Depends(get_db),
):
    alert = QualityAlert(**payload.dict())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
