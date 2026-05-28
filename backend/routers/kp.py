"""
API for commercial proposals (КП).
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.config import settings
from app.models.kp import KpDocument, KpVersion, KpTemplate, KpTemplateBinding
from app.models.lead import Lead
from app.models.lead_product import LeadProduct
from app.schemas.kp import (
    KpDocumentCreate,
    KpDocumentResponse,
    KpVersionResponse,
    KpTemplateCreate,
    KpTemplateResponse,
    KpTemplateBindingCreate,
    KpTemplateBindingResponse,
)
from app.services.storage import upload_bytes_with_safe_extension, ensure_path, clean_name
from app.utils.num2words_ru import num2text_rur
from app.core.auth_middleware import CurrentUser

router = APIRouter()


async def _next_kp_number(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(KpDocument.number_seq)))
    max_val = result.scalar()
    if max_val is None:
        return settings.KP_NUMBER_START
    return int(max_val) + 1


def _format_kp_number(seq: int) -> str:
    return f"{seq}-КП"


async def _pick_template(db: AsyncSession, our_company_id: Optional[str], template_id: Optional[str]) -> Optional[KpTemplate]:
    if template_id:
        return await db.get(KpTemplate, template_id)
    if our_company_id:
        result = await db.execute(
            select(KpTemplate)
            .join(KpTemplateBinding, KpTemplateBinding.template_id == KpTemplate.id)
            .where(
                KpTemplateBinding.our_company_id == our_company_id,
                KpTemplate.is_active == 1,
            )
        )
        tpl = result.scalars().first()
        if tpl:
            return tpl
    # fallback to any active
    result = await db.execute(select(KpTemplate).where(KpTemplate.is_active == 1).order_by(KpTemplate.created_at))
    return result.scalars().first()


async def _generate_version(
    db: AsyncSession,
    kp: KpDocument,
    template: Optional[KpTemplate],
    vat_rate: float,
) -> KpVersion:
    # Calculate totals from lead products.
    products = await LeadProduct.get_by_lead(db, kp.lead_id)
    total = sum(p.final_price or 0 for p in products)
    vat_amount = total * (vat_rate / 100.0)
    total_text = num2text_rur(total)
    vat_text = num2text_rur(vat_amount)

    version_num = (kp.current_version or 0) + 1
    version = KpVersion(
        kp_id=kp.id,
        version=version_num,
        total_amount=total,
        vat_amount=vat_amount,
        total_text=total_text,
        vat_text=vat_text,
        template_id=template.id if template else None,
    )
    db.add(version)
    kp.current_version = version_num
    kp.template_id = template.id if template else None
    kp.updated_at = datetime.now()
    await db.commit()
    await db.refresh(version)
    await db.refresh(kp)
    return version


@router.post("/kp/", response_model=KpDocumentResponse)
async def create_kp(
    payload: KpDocumentCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    seq = await _next_kp_number(db)
    number_display = _format_kp_number(seq)
    tpl = await _pick_template(db, payload.our_company_id or lead.our_company_id, payload.template_id)

    kp = KpDocument(
        lead_id=payload.lead_id,
        number_seq=seq,
        number_display=number_display,
        status="draft",
        current_version=0,
        our_company_id=payload.our_company_id or lead.our_company_id,
        template_id=tpl.id if tpl else None,
    )
    db.add(kp)
    await db.commit()
    await db.refresh(kp)

    # auto generate first version
    await _generate_version(db, kp, tpl, payload.vat_rate or 0)
    await db.refresh(kp)
    return kp


@router.get("/kp/", response_model=List[KpDocumentResponse])
async def list_kp(
    lead_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    query = select(KpDocument).options(selectinload(KpDocument.versions))
    if lead_id:
        query = query.where(KpDocument.lead_id == lead_id)
    result = await db.execute(query.order_by(KpDocument.created_at.desc()))
    return result.scalars().all()


@router.post("/kp/{kp_id}/upload", response_model=KpVersionResponse)
async def upload_kp_version(
    kp_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    kp = await db.get(KpDocument, kp_id)
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")

    # prepare storage path
    base = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    root = f"{base}/KP/{clean_name(kp.number_display)}"
    await ensure_path(root)
    content = await file.read()
    upload_res = await upload_bytes_with_safe_extension(content, root, file.filename)

    lead = await db.get(Lead, kp.lead_id)
    vat_rate = getattr(lead, "vat_rate", 0.0) or 0.0
    products = await LeadProduct.get_by_lead(db, kp.lead_id)
    total = sum(p.final_price or 0 for p in products)
    vat_amount = total * (vat_rate / 100.0)

    version_num = (kp.current_version or 0) + 1
    is_pdf = (file.filename or "").lower().endswith(".pdf")
    version = KpVersion(
        kp_id=kp.id,
        version=version_num,
        docx_url=None if is_pdf else (upload_res.public_url if upload_res else None),
        pdf_url=upload_res.public_url if is_pdf else None,
        template_id=kp.template_id,
        total_amount=total,
        vat_amount=vat_amount,
        total_text=num2text_rur(total),
        vat_text=num2text_rur(vat_amount),
    )
    db.add(version)
    kp.current_version = version_num
    kp.updated_at = datetime.now()
    await db.commit()
    await db.refresh(version)
    await db.refresh(kp)
    return version


@router.post("/kp/templates", response_model=KpTemplateResponse)
async def create_template(
    name: str = Form(...),
    docx: UploadFile = File(...),
    pdf: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    base = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    root = f"{base}/KP/templates/{clean_name(name)}"
    await ensure_path(root)
    docx_bytes = await docx.read()
    up_docx = await upload_bytes_with_safe_extension(docx_bytes, root, docx.filename)
    pdf_url = None
    if pdf:
        pdf_bytes = await pdf.read()
        up_pdf = await upload_bytes_with_safe_extension(pdf_bytes, root, pdf.filename)
        pdf_url = up_pdf.public_url if up_pdf else None

    tpl = KpTemplate(name=name, docx_url=up_docx.public_url if up_docx else "", pdf_url=pdf_url, is_active=1)
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.get("/kp/templates", response_model=List[KpTemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    res = await db.execute(select(KpTemplate).order_by(KpTemplate.created_at.desc()))
    return res.scalars().all()


@router.post("/kp/template-bindings", response_model=KpTemplateBindingResponse)
async def bind_template(
    payload: KpTemplateBindingCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(CurrentUser),
):
    tpl = await db.get(KpTemplate, payload.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    binding = KpTemplateBinding(template_id=payload.template_id, our_company_id=payload.our_company_id)
    db.add(binding)
    await db.commit()
    await db.refresh(binding)
    return binding


@router.get("/kp/template-bindings", response_model=List[KpTemplateBindingResponse])
async def list_bindings(db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    res = await db.execute(select(KpTemplateBinding))
    return res.scalars().all()


@router.get("/kp/{kp_id}", response_model=KpDocumentResponse)
async def get_kp(kp_id: str, db: AsyncSession = Depends(get_db), _: CurrentUser = Depends(CurrentUser)):
    result = await db.execute(
        select(KpDocument).where(KpDocument.id == kp_id).options(selectinload(KpDocument.versions))
    )
    kp = result.scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")
    return kp
