"""
Leads API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models import Lead, LeadProduct, Deal, DealProduct, Product
from app.schemas.lead import LeadCreate, LeadResponse
from app.services.permissions import get_section_permissions

router = APIRouter()


@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    responsible_user_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    our_company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    try:
        read_all, read_assigned = await get_section_permissions(db, user.role_id, "leads")
        if not read_all:
            if not read_assigned:
                return []
            responsible_user_id = str(user.id)
        return await Lead.get_filtered(
            db,
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            responsible_user_id=responsible_user_id,
            customer_id=customer_id,
            our_company_id=our_company_id,
        )
    except Exception as exc:
        print(f"Error getting leads: {exc}")
        return []


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    db: AsyncSession = Depends(get_db),
):
    return await Lead.create(db, **lead.dict())


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
    lead_update: dict = Body(None),
    db: AsyncSession = Depends(get_db),
):
    filtered_data = {k: v for k, v in (lead_update or {}).items() if v is not None}
    if not filtered_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    lead = await Lead.update(db, lead_id, **filtered_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await Lead.delete(db, lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
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
    return {"deal_id": str(deal.id)}
