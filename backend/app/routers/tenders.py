"""
Tenders API router.
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database.session import get_db
from app.models import (
    DealProduct,
    Deal,
    Product,
    Company,
    Tender,
    TenderOffer,
    CompanyAccreditation,
)
from app.schemas.tender import TenderCreate, TenderUpdate, TenderResponse
from app.schemas.tender_offer import TenderOfferCreate, TenderOfferUpdate, TenderOfferResponse

router = APIRouter()


def _uuid_variants(value: Optional[str]) -> List[str]:
    if not value:
        return []
    raw = str(value)
    variants = {raw}
    try:
        u = uuid.UUID(raw)
        variants.add(u.hex)
        variants.add(str(u))
    except (ValueError, TypeError):
        if len(raw) == 32:
            try:
                u = uuid.UUID(hex=raw)
                variants.add(str(u))
            except (ValueError, TypeError):
                pass
    return list(variants)


def _normalize_uuid_for_sqlite(value: Optional[str], db: AsyncSession) -> Optional[str]:
    if value is None:
        return None
    bind = db.get_bind()
    is_sqlite = bool(bind and bind.dialect.name == "sqlite")
    if not is_sqlite:
        return str(value)
    try:
        u = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return u.hex
    except (ValueError, TypeError):
        return str(value)


def _uuid_objects(values: List[str]) -> List[uuid.UUID]:
    items = []
    for value in values:
        try:
            items.append(uuid.UUID(str(value)))
        except (ValueError, TypeError):
            try:
                items.append(uuid.UUID(hex=str(value)))
            except (ValueError, TypeError):
                continue
    return items


@router.get("/items")
async def list_tender_items(
    deal_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    bind = db.get_bind()
    is_sqlite = bool(bind and bind.dialect.name == "sqlite")
    if not is_sqlite:
        query = (
            select(DealProduct, Deal, Product, Tender)
            .join(Deal, DealProduct.deal_id == Deal.id)
            .join(Product, DealProduct.product_id == Product.id)
            .outerjoin(Tender, Tender.deal_product_id == DealProduct.id)
        )
        if deal_id:
            query = query.where(Deal.id == deal_id)
        result = await db.execute(query)
        rows = result.all()

        tenders = [t for _, _, _, t in rows if t]
        tender_ids = [t.id for t in tenders]
        offers_map: Dict[str, List[TenderOffer]] = {}
        if tender_ids:
            offer_result = await db.execute(
                select(TenderOffer).where(TenderOffer.tender_id.in_(tender_ids))
            )
            for offer in offer_result.scalars().all():
                offers_map.setdefault(offer.tender_id, []).append(offer)

        company_ids = {
            t.winner_company_id for t in tenders if t and t.winner_company_id
        }
        if offers_map:
            for offers in offers_map.values():
                for offer in offers:
                    if offer.company_id:
                        company_ids.add(offer.company_id)

        company_map: Dict[str, Company] = {}
        if company_ids:
            comp_result = await db.execute(select(Company).where(Company.id.in_(list(company_ids))))
            for comp in comp_result.scalars().all():
                company_map[comp.id] = comp

        items: List[Dict[str, Any]] = []
        for deal_product, deal, product, tender in rows:
            tender_status = None
            winner_company_name = None
            winner_amount = None
            offers = offers_map.get(tender.id, []) if tender else []
            responded_count = len([o for o in offers if o.status in {"responded", "winner"}])
            if tender:
                tender_status = tender.status
                if tender.winner_company_id:
                    winner_company_name = company_map.get(tender.winner_company_id).name if company_map.get(tender.winner_company_id) else None
                    for offer in offers:
                        if offer.company_id == tender.winner_company_id:
                            winner_amount = offer.proposed_amount
                            break

            if status:
                if status == "no_tender" and tender:
                    continue
                if status != "no_tender" and tender_status != status:
                    continue

            our_price = deal_product.final_price or deal_product.total_price or 0.0
            gross_profit = None
            if winner_amount is not None:
                gross_profit = our_price - winner_amount

            items.append({
                "deal_product_id": deal_product.id,
                "deal_id": deal.id,
                "deal_title": deal.title,
                "obj_name": deal.obj_name,
                "object_area": deal.object_area,
                "object_type": deal.object_type,
                "product_id": product.id,
                "product_name": product.name,
                "direction_id": tender.direction_id if tender else str(product.category_id) if product.category_id else None,
                "our_price": our_price,
                "tender_id": tender.id if tender else None,
                "tender_status": tender_status,
                "winner_company_id": tender.winner_company_id if tender else None,
                "winner_company_name": winner_company_name,
                "winner_amount": winner_amount,
                "gross_profit": gross_profit,
                "offers_count": len(offers),
                "offers_responded": responded_count,
            })

        return items

    query = select(DealProduct)
    if deal_id:
        query = query.where(DealProduct.deal_id.in_(_uuid_variants(deal_id)))
    dp_result = await db.execute(query)
    deal_products = dp_result.scalars().all()
    if not deal_products:
        return []

    deal_ids: List[str] = []
    product_ids: List[str] = []
    deal_product_ids: List[str] = []
    for dp in deal_products:
        deal_ids.extend(_uuid_variants(dp.deal_id))
        product_ids.extend(_uuid_variants(dp.product_id))
        deal_product_ids.extend(_uuid_variants(dp.id))

    deal_map: Dict[str, Deal] = {}
    if deal_ids:
        deal_result = await db.execute(select(Deal).where(Deal.id.in_(list(set(deal_ids)))))
        for deal in deal_result.scalars().all():
            for key in _uuid_variants(deal.id):
                deal_map[key] = deal

    product_map: Dict[str, Product] = {}
    if product_ids:
        product_uuid_list = _uuid_objects(list(set(product_ids)))
        if product_uuid_list:
            product_result = await db.execute(select(Product).where(Product.id.in_(product_uuid_list)))
            for product in product_result.scalars().all():
                for key in _uuid_variants(product.id):
                    product_map[key] = product

    tender_map: Dict[str, Tender] = {}
    tender_ids: List[str] = []
    if deal_product_ids:
        tender_result = await db.execute(
            select(Tender).where(Tender.deal_product_id.in_(list(set(deal_product_ids))))
        )
        for tender in tender_result.scalars().all():
            tender_ids.append(tender.id)
            for key in _uuid_variants(tender.deal_product_id):
                tender_map[key] = tender

    offers_map: Dict[str, List[TenderOffer]] = {}
    if tender_ids:
        offer_result = await db.execute(
            select(TenderOffer).where(TenderOffer.tender_id.in_(tender_ids))
        )
        for offer in offer_result.scalars().all():
            offers_map.setdefault(offer.tender_id, []).append(offer)

    company_ids = {
        t.winner_company_id for t in tender_map.values() if t and t.winner_company_id
    }
    if offers_map:
        for offers in offers_map.values():
            for offer in offers:
                if offer.company_id:
                    company_ids.add(offer.company_id)

    company_map: Dict[str, Company] = {}
    if company_ids:
        comp_result = await db.execute(select(Company).where(Company.id.in_(list(company_ids))))
        for comp in comp_result.scalars().all():
            company_map[comp.id] = comp

    items: List[Dict[str, Any]] = []
    for deal_product in deal_products:
        tender = tender_map.get(str(deal_product.id))
        product = product_map.get(str(deal_product.product_id))
        deal = deal_map.get(str(deal_product.deal_id))

        tender_status = None
        winner_company_name = None
        winner_amount = None
        offers = offers_map.get(tender.id, []) if tender else []
        responded_count = len([o for o in offers if o.status in {"responded", "winner"}])
        if tender:
            tender_status = tender.status
            if tender.winner_company_id:
                winner_company_name = company_map.get(tender.winner_company_id).name if company_map.get(tender.winner_company_id) else None
                for offer in offers:
                    if offer.company_id == tender.winner_company_id:
                        winner_amount = offer.proposed_amount
                        break

        if status:
            if status == "no_tender" and tender:
                continue
            if status != "no_tender" and tender_status != status:
                continue

        our_price = deal_product.final_price or deal_product.total_price or 0.0
        gross_profit = None
        if winner_amount is not None:
            gross_profit = our_price - winner_amount

        items.append({
            "deal_product_id": deal_product.id,
            "deal_id": deal.id if deal else deal_product.deal_id,
            "deal_title": deal.title if deal else None,
            "obj_name": deal.obj_name if deal else None,
            "object_area": deal.object_area if deal else None,
            "object_type": deal.object_type if deal else None,
            "product_id": product.id if product else deal_product.product_id,
            "product_name": product.name if product else deal_product.custom_name,
            "direction_id": tender.direction_id if tender else str(product.category_id) if product and product.category_id else None,
            "our_price": our_price,
            "tender_id": tender.id if tender else None,
            "tender_status": tender_status,
            "winner_company_id": tender.winner_company_id if tender else None,
            "winner_company_name": winner_company_name,
            "winner_amount": winner_amount,
            "gross_profit": gross_profit,
            "offers_count": len(offers),
            "offers_responded": responded_count,
        })

    return items


@router.post("/", response_model=TenderResponse)
async def create_tender(
    payload: TenderCreate,
    db: AsyncSession = Depends(get_db),
):
    deal_product = await DealProduct.get_by_id(db, payload.deal_product_id)
    if not deal_product:
        raise HTTPException(status_code=404, detail="Deal product not found")

    existing = await db.execute(
        select(Tender).where(Tender.deal_product_id == deal_product.id)
    )
    existing_tender = existing.scalar_one_or_none()
    if existing_tender:
        # Re-sending with a deadline = "set/update the submission date".
        if payload.submission_deadline is not None:
            existing_tender.submission_deadline = payload.submission_deadline
            await db.commit()
            await db.refresh(existing_tender)
        return TenderResponse.model_validate(existing_tender)

    deal = await Deal.get_by_id(db, str(deal_product.deal_id))
    product = await Product.get_by_id(db, str(deal_product.product_id))
    if not deal or not product:
        raise HTTPException(status_code=404, detail="Deal or product not found")

    direction_id = str(product.category_id) if product.category_id else None
    tender = Tender(
        deal_product_id=_normalize_uuid_for_sqlite(deal_product.id, db),
        deal_id=_normalize_uuid_for_sqlite(deal.id, db),
        product_id=_normalize_uuid_for_sqlite(product.id, db),
        direction_id=direction_id,
        status="new",
        submission_deadline=payload.submission_deadline,
    )
    db.add(tender)
    await db.commit()
    await db.refresh(tender)

    # Auto invite accredited subcontractors
    if direction_id:
        acc_result = await db.execute(
            select(CompanyAccreditation).where(
                and_(
                    CompanyAccreditation.direction_id == direction_id,
                    CompanyAccreditation.status == "approved",
                )
            )
        )
        acc_items = acc_result.scalars().all()
        for acc in acc_items:
            offer = TenderOffer(
                tender_id=tender.id,
                company_id=acc.company_id,
                status="invited",
            )
            db.add(offer)
        await db.commit()

    return TenderResponse.model_validate(tender)


@router.patch("/{tender_id}", response_model=TenderResponse)
async def update_tender(
    tender_id: str,
    payload: TenderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Set tender fields — used for the admin "установка даты"
    (submission_deadline) and status/winner adjustments."""
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    prev_status = tender.status
    data = payload.model_dump(exclude_unset=True)
    for field in ("status", "winner_company_id", "submission_deadline"):
        if field in data:
            setattr(tender, field, data[field])
    await db.commit()
    await db.refresh(tender)

    # Event Bus v2: тендерные площадки (Госзакупки 44/223-ФЗ, B2B-Center,
    # РТС, ЭТП-Газпром) подписываются на эти события для синхронизации
    # статусов между нашим CRM и внешними системами.
    from app.services.event_outbox import emit_event_safe
    if prev_status != tender.status:
        if tender.status == "published":
            await emit_event_safe(
                db,
                event_type="tender.after_publish",
                entity_type="tender",
                entity_id=str(tender.id),
                payload={
                    "id": str(tender.id),
                    "deal_product_id": str(tender.deal_product_id) if tender.deal_product_id else None,
                    "submission_deadline": str(tender.submission_deadline) if tender.submission_deadline else None,
                },
            )
        elif tender.status in {"closed", "completed", "cancelled"}:
            await emit_event_safe(
                db,
                event_type="tender.after_close",
                entity_type="tender",
                entity_id=str(tender.id),
                payload={
                    "id": str(tender.id),
                    "status": tender.status,
                    "winner_company_id": str(tender.winner_company_id) if tender.winner_company_id else None,
                },
            )
    return TenderResponse.model_validate(tender)


@router.get("/{tender_id}")
async def get_tender(
    tender_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    offers_result = await db.execute(
        select(TenderOffer).where(TenderOffer.tender_id == tender.id)
    )
    offers = offers_result.scalars().all()
    company_ids = {o.company_id for o in offers}
    company_map: Dict[str, Company] = {}
    if company_ids:
        comp_result = await db.execute(select(Company).where(Company.id.in_(list(company_ids))))
        for comp in comp_result.scalars().all():
            company_map[comp.id] = comp

    offer_rows = []
    for offer in offers:
        company = company_map.get(offer.company_id)
        offer_rows.append({
            "id": offer.id,
            "company_id": offer.company_id,
            "company_name": company.name if company else None,
            "status": offer.status,
            "proposed_amount": offer.proposed_amount,
            "proposed_deadline": offer.proposed_deadline,
            "comment": offer.comment,
            "created_at": offer.created_at,
            "updated_at": offer.updated_at,
        })

    return {
        "tender": TenderResponse.model_validate(tender),
        "offers": offer_rows,
    }


@router.post("/{tender_id}/offers", response_model=TenderOfferResponse)
async def create_tender_offer(
    tender_id: str,
    payload: TenderOfferCreate,
    db: AsyncSession = Depends(get_db),
):
    if payload.tender_id != tender_id:
        raise HTTPException(status_code=400, detail="Tender mismatch")
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    tender = result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    existing = await db.execute(
        select(TenderOffer).where(
            and_(TenderOffer.tender_id == tender_id, TenderOffer.company_id == payload.company_id)
        )
    )
    offer = existing.scalar_one_or_none()
    if offer:
        return TenderOfferResponse.model_validate(offer)

    offer = TenderOffer(
        tender_id=tender_id,
        company_id=payload.company_id,
        status="invited",
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return TenderOfferResponse.model_validate(offer)


@router.patch("/offers/{offer_id}", response_model=TenderOfferResponse)
async def update_tender_offer(
    offer_id: str,
    payload: TenderOfferUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TenderOffer).where(TenderOffer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data.get("status") == "responded":
        if update_data.get("proposed_amount") is None and offer.proposed_amount is None:
            raise HTTPException(status_code=400, detail="Amount is required to respond")

    for key, value in update_data.items():
        setattr(offer, key, value)

    await db.commit()
    await db.refresh(offer)

    if offer.status == "responded":
        tender_result = await db.execute(select(Tender).where(Tender.id == offer.tender_id))
        tender = tender_result.scalar_one_or_none()
        if tender and tender.status == "new":
            tender.status = "review"
            await db.commit()

    return TenderOfferResponse.model_validate(offer)


@router.post("/{tender_id}/select-winner")
async def select_winner(
    tender_id: str,
    offer_id: str,
    db: AsyncSession = Depends(get_db),
):
    tender_result = await db.execute(select(Tender).where(Tender.id == tender_id))
    tender = tender_result.scalar_one_or_none()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    offer_result = await db.execute(select(TenderOffer).where(TenderOffer.id == offer_id))
    offer = offer_result.scalar_one_or_none()
    if not offer or offer.tender_id != tender_id:
        raise HTTPException(status_code=404, detail="Offer not found")

    tender.winner_company_id = offer.company_id
    tender.status = "archived"

    offers_result = await db.execute(
        select(TenderOffer).where(TenderOffer.tender_id == tender_id)
    )
    offers = offers_result.scalars().all()
    accepted_offer_id = None
    rejected_offer_ids = []
    for item in offers:
        if item.id == offer_id:
            item.status = "winner"
            accepted_offer_id = str(item.id)
        else:
            item.status = "rejected"
            rejected_offer_ids.append(str(item.id))

    await db.commit()

    # Event Bus v2: tender_offer.after_accept (победитель) + N×reject.
    # Тендерные площадки слушают эти события для обновления статусов
    # в Госзакупках / B2B-Center / РТС.
    from app.services.event_outbox import emit_event_safe
    if accepted_offer_id:
        await emit_event_safe(
            db,
            event_type="tender_offer.after_accept",
            entity_type="tender_offer",
            entity_id=accepted_offer_id,
            payload={
                "id": accepted_offer_id,
                "tender_id": str(tender_id),
                "company_id": str(offer.company_id) if offer.company_id else None,
                "proposed_amount": float(offer.proposed_amount or 0),
            },
        )
    for rid in rejected_offer_ids:
        await emit_event_safe(
            db,
            event_type="tender_offer.after_reject",
            entity_type="tender_offer",
            entity_id=rid,
            payload={
                "id": rid,
                "tender_id": str(tender_id),
            },
        )
    return {"status": "ok"}


@router.get("/company/{company_id}")
async def list_company_tenders(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(TenderOffer, Tender)
            .join(Tender, TenderOffer.tender_id == Tender.id)
            .where(TenderOffer.company_id == company_id)
        )
        rows = result.all()

        tenders = [t for _, t in rows]
        deal_ids: List[str] = []
        deal_product_ids: List[str] = []
        product_ids: List[str] = []
        for tender in tenders:
            deal_ids.extend(_uuid_variants(tender.deal_id))
            deal_product_ids.extend(_uuid_variants(tender.deal_product_id))
            product_ids.extend(_uuid_variants(tender.product_id))

        deal_map: Dict[str, Deal] = {}
        if deal_ids:
            deal_result = await db.execute(select(Deal).where(Deal.id.in_(list(set(deal_ids)))))
            for deal in deal_result.scalars().all():
                for key in _uuid_variants(deal.id):
                    deal_map[key] = deal

        product_map: Dict[str, Product] = {}
        if product_ids:
            product_uuid_list = _uuid_objects(list(set(product_ids)))
            if product_uuid_list:
                product_result = await db.execute(select(Product).where(Product.id.in_(product_uuid_list)))
            else:
                product_result = None
            if product_result is None:
                products = []
            else:
                products = product_result.scalars().all()
            for product in products:
                for key in _uuid_variants(product.id):
                    product_map[key] = product

        deal_product_map: Dict[str, DealProduct] = {}
        if deal_product_ids:
            dp_result = await db.execute(select(DealProduct).where(DealProduct.id.in_(list(set(deal_product_ids)))))
            for dp in dp_result.scalars().all():
                for key in _uuid_variants(dp.id):
                    deal_product_map[key] = dp

        def _deadline_passed(dt) -> bool:
            if not dt:
                return False
            try:
                now = datetime.now(timezone.utc)
                if getattr(dt, "tzinfo", None) is None:
                    # Naive (sqlite) — compare against naive UTC now.
                    return dt < now.replace(tzinfo=None)
                return dt < now
            except Exception:
                return False

        # Offer counts as "submitted" once the subcontractor has responded
        # (or already won). invited/rejected/empty = not submitted.
        SUBMITTED = {"responded", "winner"}

        items: List[Dict[str, Any]] = []
        for offer, tender in rows:
            deal = deal_map.get(str(tender.deal_id))
            product = product_map.get(str(tender.product_id))
            deal_product = deal_product_map.get(str(tender.deal_product_id))
            has_submitted = offer.status in SUBMITTED
            # Past deadline + this company didn't submit -> intake closed,
            # tender no longer active for them (those who bid still see it).
            submission_closed = (
                _deadline_passed(tender.submission_deadline) and not has_submitted
            )
            items.append({
                "tender_id": tender.id,
                "tender_status": tender.status,
                "offer_id": offer.id,
                "offer_status": offer.status,
                "proposed_amount": offer.proposed_amount,
                "proposed_deadline": offer.proposed_deadline,
                "comment": offer.comment,
                "deal_title": deal.title if deal else None,
                "obj_name": deal.obj_name if deal else None,
                "object_area": deal.object_area if deal else None,
                "object_type": deal.object_type if deal else None,
                "product_name": product.name if product else None,
                "our_price": (deal_product.final_price or deal_product.total_price or 0.0) if deal_product else 0.0,
                "direction_id": tender.direction_id,
                "submission_deadline": tender.submission_deadline,
                "submission_closed": submission_closed,
            })

        return items
    except Exception as exc:
        print(f"Error listing company tenders: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
