"""
Customer portal API router.
"""
from __future__ import annotations

import mimetypes
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import String, and_, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Company, CompanyUserLink, Deal, DealProduct, IncomeExpenseEntry, OutgoingDocument, User
from app.routers.contracts import _build_payment_responses
from app.routers.deal_execution import get_defacto_view
from app.routers.deals import _build_root_paths
from app.routers.outgoing_registry import (
    _build_outgoing_file_base_clean,
    _company_label,
    _content_disposition,
    _resolve_effective_render_payload,
    _serialize_document,
)
from app.services.storage import _local_path, clean_name, is_local_storage, list_items, read_file_bytes, storage_available


router = APIRouter()

_DOC_SECTIONS = {"tz", "other", "results"}


def _normalize_uuid_variants(*values: Iterable[str]) -> List[str]:
    variants: List[str] = []
    seen = set()
    for value in values:
        if value in (None, ""):
            continue
        try:
            parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
            current = [str(parsed), parsed.hex]
        except (ValueError, TypeError):
            current = [str(value)]
        for item in current:
            if item in seen:
                continue
            seen.add(item)
            variants.append(item)
    return variants


def _id_in_conditions(column, *values):
    variants = _normalize_uuid_variants(*values)
    if not variants:
        return cast(column, String).in_(["__never_match__"])
    return cast(column, String).in_(variants)


async def _customer_company_ids(db: AsyncSession, user_id: str) -> List[str]:
    result = await db.execute(
        select(CompanyUserLink.company_id)
        .join(Company, CompanyUserLink.company_id == Company.id)
        .where(
            _id_in_conditions(CompanyUserLink.user_id, user_id),
            Company.type == "customer",
            CompanyUserLink.link_type.in_(["leader", "employee", "customer"]),
        )
    )
    company_ids = []
    seen = set()
    for company_id in result.scalars().all():
        normalized = str(company_id)
        if normalized in seen:
            continue
        seen.add(normalized)
        company_ids.append(normalized)
    return company_ids


async def _customer_deal_or_404(db: AsyncSession, user: User, deal_id: str) -> Deal:
    company_ids = await _customer_company_ids(db, str(user.id))
    if not company_ids:
        raise HTTPException(status_code=404, detail="Проект не найден")

    result = await db.execute(
        select(Deal).where(
            _id_in_conditions(Deal.id, deal_id),
            _id_in_conditions(Deal.customer_id, *company_ids),
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return deal


async def _company_map_for_deals(db: AsyncSession, deals: List[Deal]) -> Dict[str, Company]:
    company_ids = {
        str(company_id)
        for deal in deals
        for company_id in (deal.customer_id, deal.our_company_id)
        if company_id
    }
    if not company_ids:
        return {}
    result = await db.execute(select(Company).where(_id_in_conditions(Company.id, *company_ids)))
    return {str(company.id): company for company in result.scalars().all()}


def _deal_summary_payload(deal: Deal, company_map: Dict[str, Company]) -> dict:
    customer = company_map.get(str(deal.customer_id)) if deal.customer_id else None
    our_company = company_map.get(str(deal.our_company_id)) if deal.our_company_id else None
    return {
        "id": str(deal.id),
        "title": deal.title,
        "obj_name": deal.obj_name,
        "address": deal.address,
        "status": deal.status,
        "customer_id": str(deal.customer_id) if deal.customer_id else None,
        "customer_name": customer.name if customer else None,
        "our_company_id": str(deal.our_company_id) if deal.our_company_id else None,
        "our_company_name": our_company.name if our_company else None,
        "total_contract_value": float(deal.total_contract_value or 0),
        "total_paid": float(deal.total_paid or 0),
    }


async def _deal_products_payload(db: AsyncSession, deal_id: str) -> List[dict]:
    products = await DealProduct.get_by_deal(db, deal_id)
    payload = []
    for item in products:
        payload.append(
            {
                "id": str(item.id),
                "name": item.custom_name or (item.product.name if item.product else "Без названия"),
                "quantity": float(item.quantity or 0),
                "unit": item.unit or "",
                "unit_price": float(item.unit_price or 0),
                "tax_rate": float(item.tax_rate or 0),
                "final_price": float(item.final_price or 0),
                "status": item.status or "planned",
            }
        )
    payload.sort(key=lambda item: str(item["name"]).lower())
    return payload


async def _deal_payments_payload(db: AsyncSession, deal: Deal) -> tuple[List[dict], dict]:
    result = await db.execute(
        select(IncomeExpenseEntry)
        .where(_id_in_conditions(IncomeExpenseEntry.deal_id, deal.id))
        .order_by(IncomeExpenseEntry.plan_date.desc(), IncomeExpenseEntry.created_at.desc())
    )
    entries = [
        entry
        for entry in result.scalars().all()
        if str(entry.payer_id or "") == str(deal.customer_id or "") or str(entry.payee_id or "") == str(deal.customer_id or "")
    ]
    responses = await _build_payment_responses(db, entries)
    total_amount = sum(float(item.amount or 0) for item in responses)
    paid_amount = sum(float(item.paid_amount or 0) for item in responses)
    pending_amount = max(total_amount - paid_amount, 0.0)
    return [item.model_dump() for item in responses], {
        "count": len(responses),
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
    }


async def _deal_letters_payload(db: AsyncSession, deal: Deal) -> List[dict]:
    result = await db.execute(
        select(OutgoingDocument)
        .where(
            and_(
                _id_in_conditions(OutgoingDocument.deal_id, deal.id),
                _id_in_conditions(OutgoingDocument.recipient_company_id, deal.customer_id),
            )
        )
        .order_by(OutgoingDocument.letter_date.desc(), OutgoingDocument.created_at.desc())
    )
    letters = []
    for document in result.scalars().all():
        serialized = await _serialize_document(db, document, include_details=True)
        latest_file = next(
            (
                file
                for file in serialized.files
                if file.file_type in {"pdf_current", "pdf_version", "pdf_attachment"}
            ),
            None,
        )
        letters.append(
            {
                "id": serialized.id,
                "outgoing_number": serialized.outgoing_number_display or serialized.outgoing_number,
                "letter_date": serialized.letter_date,
                "subject": serialized.subject,
                "status": serialized.status,
                "our_company_key": serialized.our_company_key,
                "our_company_label": _company_label(serialized.our_company_key),
                "file_name": latest_file.file_name if latest_file else clean_name(f"{_build_outgoing_file_base_clean(document)}.pdf"),
            }
        )
    return letters


def _resolve_customer_storage_path(root_path: str, current_path: str | None = None) -> str:
    requested_path = current_path or root_path
    root_local = _local_path(root_path).resolve(strict=False)
    requested_local = _local_path(requested_path).resolve(strict=False)
    try:
        requested_local.relative_to(root_local)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Недопустимый путь") from exc
    return requested_path


@router.get("/projects")
async def customer_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    company_ids = await _customer_company_ids(db, str(user.id))
    if not company_ids:
        return []
    result = await db.execute(
        select(Deal)
        .where(_id_in_conditions(Deal.customer_id, *company_ids))
        .order_by(Deal.title.asc())
    )
    deals = result.scalars().all()
    company_map = await _company_map_for_deals(db, deals)
    return [_deal_summary_payload(deal, company_map) for deal in deals]


@router.get("/projects/{deal_id}")
async def customer_project_detail(
    deal_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _customer_deal_or_404(db, user, deal_id)
    company_map = await _company_map_for_deals(db, [deal])
    products = await _deal_products_payload(db, str(deal.id))
    payments, payment_summary = await _deal_payments_payload(db, deal)
    letters = await _deal_letters_payload(db, deal)
    execution = await get_defacto_view(str(deal.id), db)
    return {
        "deal": _deal_summary_payload(deal, company_map),
        "products": products,
        "payments": payments,
        "payment_summary": payment_summary,
        "execution": execution,
        "letters": letters,
        "document_sections": [
            {"key": "tz", "label": "ТЗ"},
            {"key": "other", "label": "Документация"},
            {"key": "results", "label": "Результаты"},
        ],
    }


@router.get("/projects/{deal_id}/storage/list")
async def customer_project_storage_list(
    deal_id: str,
    section: str = Query(...),
    path: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if section not in _DOC_SECTIONS:
        raise HTTPException(status_code=400, detail="Неизвестный раздел документов")
    if not storage_available():
        raise HTTPException(status_code=500, detail="Хранилище не настроено")

    deal = await _customer_deal_or_404(db, user, deal_id)
    roots = _build_root_paths(str(deal.id), deal.title)
    root_path = roots[section]
    current_path = _resolve_customer_storage_path(root_path, path)
    return {
        "section": section,
        "root_path": root_path,
        "current_path": current_path,
        "items": await list_items(current_path, limit=200),
    }


@router.get("/projects/{deal_id}/storage/download")
async def customer_project_storage_download(
    deal_id: str,
    section: str = Query(...),
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if section not in _DOC_SECTIONS:
        raise HTTPException(status_code=400, detail="Неизвестный раздел документов")
    if not storage_available():
        raise HTTPException(status_code=500, detail="Хранилище не настроено")

    deal = await _customer_deal_or_404(db, user, deal_id)
    roots = _build_root_paths(str(deal.id), deal.title)
    root_path = roots[section]
    current_path = _resolve_customer_storage_path(root_path, path)

    filename = Path(current_path).name or "file"
    mime_type, _ = mimetypes.guess_type(filename)
    if is_local_storage():
        local_path = _local_path(current_path)
        if local_path.exists() and local_path.is_dir():
            zip_name = f"{filename}.zip" if not filename.lower().endswith(".zip") else filename
            tmp_dir = tempfile.mkdtemp(prefix="crm_customer_zip_")
            archive_base = os.path.join(tmp_dir, "archive")
            shutil.make_archive(archive_base, "zip", root_dir=local_path.parent, base_dir=local_path.name)
            zip_path = archive_base + ".zip"
            headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(zip_name, safe='')}"}
            return FileResponse(
                zip_path,
                media_type="application/zip",
                headers=headers,
                background=BackgroundTask(shutil.rmtree, tmp_dir, ignore_errors=True),
            )

    try:
        content = await read_file_bytes(current_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Файл не найден") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Не удалось скачать файл") from exc

    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"}
    return Response(content=content, media_type=mime_type or "application/octet-stream", headers=headers)


@router.get("/projects/{deal_id}/letters/{letter_id}/download")
async def customer_project_letter_download(
    deal_id: str,
    letter_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _customer_deal_or_404(db, user, deal_id)
    result = await db.execute(
        select(OutgoingDocument).where(
            and_(
                _id_in_conditions(OutgoingDocument.id, letter_id),
                _id_in_conditions(OutgoingDocument.deal_id, deal.id),
                _id_in_conditions(OutgoingDocument.recipient_company_id, deal.customer_id),
            )
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Письмо не найдено")

    effective_render = await _resolve_effective_render_payload(db, document)
    pdf_bytes = effective_render["pdf_bytes"]
    if pdf_bytes is None:
        raise HTTPException(status_code=409, detail="Файл письма недоступен")

    filename = effective_render["pdf_filename"] or clean_name(f"{_build_outgoing_file_base_clean(document)}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": _content_disposition("attachment", filename),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
