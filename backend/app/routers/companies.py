"""
Companies (Контрагенты) API Router
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
import httpx

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.models import Company, CompanyDocument, CompanyUserLink, Deal, User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.schemas.company_document import CompanyDocumentResponse
from app.services.storage import delete_path, get_download_href, storage_available, upload_file_with_safe_extension
from app.services.upload_security import validate_upload_metadata, write_upload_to_tmp
from app.services.permissions import allowed_deal_ids, get_section_permissions, require_section_write

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    company_type: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_dir: Optional[str] = "asc",
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    """Получить список всех компаний"""
    try:
        companies = await Company.get_all(
            db, skip=skip, limit=limit, search=search, 
            company_type=company_type, sort_by=sort_by, sort_dir=sort_dir
        )
        read_all, read_assigned = await get_section_permissions(db, user.role_id, "companies")
        if not read_all:
            if not read_assigned:
                return []
            allowed = await allowed_deal_ids(db, request, user)
            if allowed == []:
                return []
            result = await db.execute(select(Deal).where(Deal.id.in_(allowed)))
            deals = result.scalars().all()
            company_ids = {
                str(value)
                for deal in deals
                for value in (deal.customer_id, deal.our_company_id, deal.general_contractor_id)
                if value
            }
            if not company_ids:
                return []
            companies = [c for c in companies if str(c.id) in company_ids]
        return companies
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []

@router.get("/count")
async def get_companies_count(
    search: Optional[str] = None,
    company_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить количество компаний с фильтрами"""
    try:
        count = await Company.get_count(db, search=search, company_type=company_type)
        return {"count": count}
    except Exception as e:
        print(f"Error getting companies count: {e}")
        return {"count": 0}


@router.get("/types-summary")
async def get_companies_types_summary(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(CurrentUser),
):
    """Распределение количества контрагентов по типам (для chip-фильтров)."""
    try:
        from sqlalchemy import select as _select, func as _func
        query = _select(Company.type, _func.count(Company.id)).group_by(Company.type)
        if search:
            like = f"%{search.strip()}%"
            from sqlalchemy import or_
            query = query.where(
                or_(
                    Company.name.ilike(like),
                    Company.short_name.ilike(like),
                    Company.full_name.ilike(like),
                    Company.inn.ilike(like),
                    Company.contact_person.ilike(like),
                )
            )
        result = await db.execute(query)
        rows = result.all()
        counts = {row[0] or 'other': int(row[1] or 0) for row in rows}
        total = sum(counts.values())
        return {"total": total, "counts": counts}
    except Exception as e:
        print(f"Error in types-summary: {e}")
        return {"total": 0, "counts": {}}


@router.get("/default-our-company")
async def get_default_our_company(
    db: AsyncSession = Depends(get_db),
    _=Depends(CurrentUser),
):
    """Returns the system-wide "наша компания" default — the company whose
    is_default flag is set. Frontend uses this to display the implicit
    "our company" on detail pages (since the picker is gone).
    Returns 404 if no default is set yet."""
    company = await Company.get_default_our_company(db)
    if not company:
        raise HTTPException(status_code=404, detail="Default our company is not configured")
    return company


@router.post("/{company_id}/set-default", response_model=CompanyResponse)
async def set_default_our_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("companies")),
):
    """Mark this company as the default "наша компания". Only internal
    companies are allowed. Atomically clears the flag on all others."""
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if (company.type or "").lower() != "internal":
        raise HTTPException(
            status_code=400,
            detail="Only internal companies can be set as default our_company",
        )
    return await Company.set_default(db, company_id)


@router.get("/{company_id}/related-deals")
async def get_company_related_deals(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(CurrentUser),
):
    """Сделки, где компания фигурирует как заказчик/наша/генподрядчик."""
    try:
        from sqlalchemy import or_, select as _select
        result = await db.execute(
            _select(Deal).where(
                or_(
                    Deal.customer_id == company_id,
                    Deal.our_company_id == company_id,
                    Deal.general_contractor_id == company_id,
                )
            ).order_by(Deal.created_at.desc()).limit(200)
        )
        items = result.scalars().all()
        return [
            {
                "id": str(deal.id),
                "title": deal.title,
                "status": deal.status,
                "created_at": deal.created_at,
                "role": (
                    "customer" if str(deal.customer_id or '') == str(company_id)
                    else "our" if str(deal.our_company_id or '') == str(company_id)
                    else "contractor" if str(deal.general_contractor_id or '') == str(company_id)
                    else "other"
                ),
            }
            for deal in items
        ]
    except Exception as e:
        print(f"Error in related-deals: {e}")
        return []

async def _lookup_party(inn: str, client: httpx.AsyncClient, token: str) -> dict:
    """Запрос данных компании через DaData по ИНН."""
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {token}",
    }
    resp = await client.post(url, json={"query": inn, "branch_type": "MAIN"}, headers=headers)
    if resp.status_code >= 400:
        return {}
    suggestions = resp.json().get("suggestions") or []
    if not suggestions:
        return {}
    suggestion = suggestions[0]
    data = suggestion.get("data") or {}
    name_data = data.get("name") or {}

    ceo_name = None
    management = data.get("management") or {}
    if management.get("name"):
        ceo_name = management["name"]
    else:
        fio = data.get("fio") or {}
        parts = [fio.get("surname"), fio.get("name"), fio.get("patronymic")]
        fio_value = " ".join([p for p in parts if p])
        if fio_value:
            ceo_name = fio_value

    address_data = data.get("address") or {}

    return {
        "short_name": name_data.get("short_with_opf") or name_data.get("short") or suggestion.get("value"),
        "full_name": name_data.get("full_with_opf") or name_data.get("full") or suggestion.get("value"),
        "kpp": data.get("kpp"),
        "ceo_name": ceo_name,
        "address": address_data.get("value"),
    }


async def _ensure_company_visible(
    company_id: str,
    request: Request,
    db: AsyncSession,
    user,
) -> Company:
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "companies")
    if read_all:
        return company
    if not read_assigned:
        raise HTTPException(status_code=404, detail="Company not found")

    allowed = await allowed_deal_ids(db, request, user)
    if allowed == []:
        raise HTTPException(status_code=404, detail="Company not found")
    if allowed is None:
        return company

    result = await db.execute(select(Deal).where(Deal.id.in_(allowed)))
    deals = result.scalars().all()
    company_ids = {
        str(value)
        for deal in deals
        for value in (deal.customer_id, deal.our_company_id, deal.general_contractor_id)
        if value
    }
    if str(company.id) not in company_ids:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _company_document_response(document: CompanyDocument, our_company_name: Optional[str] = None) -> dict:
    payload = CompanyDocumentResponse.model_validate(document).model_dump()
    payload["our_company_name"] = our_company_name
    return payload


@router.post("/refresh-all")
async def refresh_all_companies(
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("companies")),
):
    """Обновить данные всех компаний через DaData по ИНН."""
    token = settings.DADATA_TOKEN
    if not token:
        raise HTTPException(status_code=500, detail="Dadata token is not configured")

    result = await db.execute(select(Company))
    all_companies = result.scalars().all()

    updated = 0
    skipped = 0
    errors = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for company in all_companies:
            inn = (company.inn or "").strip()
            if not inn or len(inn) < 10:
                skipped += 1
                continue

            try:
                data = await _lookup_party(inn, client, token)
                if not data or (not data.get("short_name") and not data.get("full_name")):
                    skipped += 1
                    continue

                changed = False
                if data.get("short_name") and data["short_name"] != company.short_name:
                    company.short_name = data["short_name"]
                    if not company.name or company.name == company.short_name:
                        company.name = data["short_name"]
                    changed = True
                if data.get("full_name") and data["full_name"] != company.full_name:
                    company.full_name = data["full_name"]
                    changed = True
                if data.get("kpp") and data["kpp"] != getattr(company, "kpp", None):
                    company.kpp = data["kpp"]
                    changed = True
                if data.get("ceo_name") and data["ceo_name"] != company.contact_person:
                    company.contact_person = data["ceo_name"]
                    changed = True
                if data.get("address") and data["address"] != company.address:
                    company.address = data["address"]
                    changed = True

                if changed:
                    updated += 1
                else:
                    skipped += 1

                # Rate limit: DaData free tier ~30 req/sec
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.warning(f"Refresh failed for company {company.id} (INN={inn}): {e}")
                errors += 1

    await db.commit()

    return {
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "total": len(all_companies),
    }


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("companies")),
):
    """Создать новую компанию"""
    db_company = await Company.create(db, **company.dict())
    return db_company


@router.get("/{company_id}/documents", response_model=List[CompanyDocumentResponse])
async def list_company_documents(
    company_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    await _ensure_company_visible(company_id, request, db, user)
    OurCompany = aliased(Company)
    result = await db.execute(
        select(CompanyDocument, OurCompany.name)
        .outerjoin(OurCompany, CompanyDocument.our_company_id == OurCompany.id)
        .where(
            CompanyDocument.company_id == company_id,
            CompanyDocument.doc_type == "company_file",
        )
        .order_by(CompanyDocument.created_at.desc())
    )
    return [
        _company_document_response(document, our_company_name)
        for document, our_company_name in result.all()
    ]


@router.post("/{company_id}/documents/upload", response_model=CompanyDocumentResponse)
async def upload_company_file_document(
    company_id: str,
    request: Request,
    our_company_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("companies")),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    await _ensure_company_visible(company_id, request, db, user)

    # Frontend dropped the "our company" picker — fall back to the
    # system default when nothing is sent.
    if not our_company_id:
        our_company_id = await Company.get_default_our_company_id(db)
    if not our_company_id:
        raise HTTPException(
            status_code=400,
            detail="Default our_company is not configured; set one via /companies/{id}/set-default",
        )
    our_company = await Company.get_by_id(db, our_company_id)
    if not our_company:
        raise HTTPException(status_code=400, detail="Our company not found")

    safe_name = validate_upload_metadata(file.filename, file.content_type)
    temp_path, size_bytes = await write_upload_to_tmp(
        file,
        int(settings.UPLOAD_TMP_MAX_BYTES or 256 * 1024 * 1024),
    )
    storage_path = f"/companies/{company_id}/documents/{uuid.uuid4()}_{safe_name}"
    try:
        await upload_file_with_safe_extension(storage_path, temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)
        await file.close()

    document = CompanyDocument(
        company_id=company_id,
        our_company_id=our_company_id,
        doc_type="company_file",
        file_name=safe_name,
        storage_path=storage_path,
        file_size=size_bytes,
        content_type=file.content_type,
        status="approved",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return _company_document_response(document, our_company.name)


@router.get("/documents/{document_id}/download")
async def download_company_file_document(
    document_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    result = await db.execute(
        select(CompanyDocument).where(
            CompanyDocument.id == document_id,
            CompanyDocument.doc_type == "company_file",
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    await _ensure_company_visible(str(document.company_id), request, db, user)
    if not document.storage_path:
        raise HTTPException(status_code=400, detail="Document does not have storage path")

    href = await get_download_href(document.storage_path)
    return {"href": href}


@router.delete("/documents/{document_id}")
async def delete_company_file_document(
    document_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("companies")),
):
    result = await db.execute(
        select(CompanyDocument).where(
            CompanyDocument.id == document_id,
            CompanyDocument.doc_type == "company_file",
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    await _ensure_company_visible(str(document.company_id), request, db, user)

    if document.storage_path:
        try:
            await delete_path(document.storage_path)
        except Exception as exc:
            logger.warning("Failed to delete company document file %s: %s", document.id, exc)
    await db.delete(document)
    await db.commit()
    return {"deleted": True}


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    """Получить компанию по ID"""
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "companies")
    if not read_all:
        if not read_assigned:
            raise HTTPException(status_code=404, detail="РљРѕРјРїР°РЅРёСЏ РЅРµ РЅР°Р№РґРµРЅР°")
        allowed = await allowed_deal_ids(db, request, user)
        if allowed is not None:
            result = await db.execute(select(Deal).where(Deal.id.in_(allowed)))
            deals = result.scalars().all()
            company_ids = {
                str(value)
                for deal in deals
                for value in (deal.customer_id, deal.our_company_id, deal.general_contractor_id)
                if value
            }
            if str(company.id) not in company_ids:
                raise HTTPException(status_code=404, detail="РљРѕРјРїР°РЅРёСЏ РЅРµ РЅР°Р№РґРµРЅР°")
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("companies")),
):
    """Обновить компанию"""
    company = await Company.update(db, company_id, **company_update.dict(exclude_unset=True))
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return company

@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("companies")),
):
    """Удалить компанию"""
    success = await Company.delete(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return {"message": "Компания удалена"}


@router.get("/{company_id}/users")
async def get_company_users(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    links = await CompanyUserLink.get_by_company(db, company_id)
    user_ids = [str(link.user_id) for link in links]
    users = []
    if user_ids:
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = result.scalars().all()
    user_map = {str(u.id): u for u in users}
    leaders = []
    employees = []
    for link in links:
        user = user_map.get(str(link.user_id))
        if not user:
            continue
        entry = {"id": str(user.id), "full_name": user.full_name, "email": user.email}
        if link.link_type == "leader":
            leaders.append(entry)
        elif link.link_type == "employee":
            employees.append(entry)
    return {"leaders": leaders, "employees": employees}


@router.put("/{company_id}/users")
async def set_company_users(
    company_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("companies")),
):
    company = await Company.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    leaders = payload.get("leader_user_ids") or []
    employees = payload.get("employee_user_ids") or []
    all_ids = list({*leaders, *employees})
    if all_ids:
        result = await db.execute(select(User).where(User.id.in_(all_ids)))
        users = result.scalars().all()
        if len(users) != len(all_ids):
            raise HTTPException(status_code=400, detail="Invalid user id in payload")
    await db.execute(delete(CompanyUserLink).where(CompanyUserLink.company_id == str(company_id)))
    for user_id in leaders:
        db.add(CompanyUserLink(company_id=str(company_id), user_id=user_id, link_type="leader"))
    for user_id in employees:
        db.add(CompanyUserLink(company_id=str(company_id), user_id=user_id, link_type="employee"))
    await db.commit()
    return {"message": "Company users updated"}
