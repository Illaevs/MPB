"""
Accreditations and documents API router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.session import get_db
from app.models import CompanyAccreditation, CompanyDocument
from app.services.storage import clean_name, ensure_path, upload_bytes_with_safe_extension, get_download_href, storage_available
from app.core.config import settings
from app.schemas.accreditation import (
    AccreditationCreate,
    AccreditationUpdate,
    AccreditationRequest,
    AccreditationBulkAction,
    AccreditationResponse,
)
from app.schemas.company_document import (
    CompanyDocumentCreate,
    CompanyDocumentUpdate,
    CompanyDocumentResponse,
)

router = APIRouter()


@router.get("/", response_model=List[AccreditationResponse])
async def list_accreditations(
    company_id: Optional[str] = None,
    direction_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(CompanyAccreditation)
    if company_id:
        query = query.where(CompanyAccreditation.company_id == company_id)
    if direction_id:
        query = query.where(CompanyAccreditation.direction_id == direction_id)
    if status:
        query = query.where(CompanyAccreditation.status == status)
    result = await db.execute(query)
    return [AccreditationResponse.model_validate(item) for item in result.scalars().all()]


@router.post("/", response_model=AccreditationResponse)
async def create_accreditation(
    payload: AccreditationCreate,
    db: AsyncSession = Depends(get_db),
):
    acc = CompanyAccreditation(
        company_id=payload.company_id,
        direction_id=payload.direction_id,
        status=payload.status or "pending",
        comment=payload.comment,
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return AccreditationResponse.model_validate(acc)


@router.post("/request")
async def request_accreditations(
    payload: AccreditationRequest,
    db: AsyncSession = Depends(get_db),
):
    created = 0
    updated = 0
    for direction_id in payload.direction_ids:
        result = await db.execute(
            select(CompanyAccreditation).where(
                and_(
                    CompanyAccreditation.company_id == payload.company_id,
                    CompanyAccreditation.direction_id == direction_id,
                )
            )
        )
        acc = result.scalar_one_or_none()
        if acc:
            if acc.status != "approved":
                acc.status = "pending"
                acc.comment = None
                updated += 1
        else:
            acc = CompanyAccreditation(
                company_id=payload.company_id,
                direction_id=direction_id,
                status="pending",
            )
            db.add(acc)
            created += 1
    await db.commit()
    return {"created": created, "updated": updated}


@router.get("/accredited-company-ids", response_model=List[str])
async def accredited_company_ids(
    direction_ids: str,
    status: str = "approved",
    db: AsyncSession = Depends(get_db),
):
    """Company ids that have `status` accreditation in **every** direction
    of the comma-separated `direction_ids` (match-all). Powers the admin
    "filter by accredited directions" — pick several directions, get only
    companies accredited across all of them."""
    wanted = [d.strip() for d in (direction_ids or "").split(",") if d.strip()]
    if not wanted:
        return []
    result = await db.execute(
        select(
            CompanyAccreditation.company_id,
            CompanyAccreditation.direction_id,
        ).where(
            and_(
                CompanyAccreditation.status == status,
                CompanyAccreditation.direction_id.in_(wanted),
            )
        )
    )
    by_company: dict = {}
    for company_id, direction_id in result.all():
        by_company.setdefault(str(company_id), set()).add(str(direction_id))
    wanted_set = set(wanted)
    return [cid for cid, dirs in by_company.items() if wanted_set.issubset(dirs)]


@router.post("/bulk")
async def bulk_update_accreditations(
    payload: AccreditationBulkAction,
    db: AsyncSession = Depends(get_db),
):
    """Bulk approve/reject accreditation records by id."""
    new_status = (payload.status or "").strip()
    if new_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")
    if new_status == "rejected" and not (payload.comment or "").strip():
        raise HTTPException(status_code=400, detail="Comment is required for rejection")
    if not payload.ids:
        return {"updated": 0}
    result = await db.execute(
        select(CompanyAccreditation).where(CompanyAccreditation.id.in_(payload.ids))
    )
    rows = result.scalars().all()
    for acc in rows:
        acc.status = new_status
        acc.comment = payload.comment if new_status == "rejected" else None
    await db.commit()
    return {"updated": len(rows)}


@router.post("/bulk-directions")
async def bulk_set_company_directions(
    payload: AccreditationRequest,
    status: str = "approved",
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Admin bulk approve/reject several DIRECTIONS for one company,
    upserting (a direction never requested still gets a record). Powers
    the admin bulk editor (checkboxes on the directions table)."""
    new_status = (status or "").strip()
    if new_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")
    if new_status == "rejected" and not (comment or "").strip():
        raise HTTPException(status_code=400, detail="Comment is required for rejection")
    created = 0
    updated = 0
    for direction_id in payload.direction_ids:
        result = await db.execute(
            select(CompanyAccreditation).where(
                and_(
                    CompanyAccreditation.company_id == payload.company_id,
                    CompanyAccreditation.direction_id == direction_id,
                )
            )
        )
        acc = result.scalar_one_or_none()
        if acc:
            acc.status = new_status
            acc.comment = comment if new_status == "rejected" else None
            updated += 1
        else:
            db.add(CompanyAccreditation(
                company_id=payload.company_id,
                direction_id=direction_id,
                status=new_status,
                comment=comment if new_status == "rejected" else None,
            ))
            created += 1
    await db.commit()
    return {"created": created, "updated": updated}


@router.patch("/{accreditation_id}", response_model=AccreditationResponse)
async def update_accreditation(
    accreditation_id: str,
    payload: AccreditationUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompanyAccreditation).where(CompanyAccreditation.id == accreditation_id)
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Accreditation not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data.get("status") == "rejected" and not update_data.get("comment"):
        raise HTTPException(status_code=400, detail="Comment is required for rejection")

    for key, value in update_data.items():
        setattr(acc, key, value)

    await db.commit()
    await db.refresh(acc)
    return AccreditationResponse.model_validate(acc)


@router.get("/companies/{company_id}/documents", response_model=List[CompanyDocumentResponse])
async def list_company_documents(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompanyDocument).where(CompanyDocument.company_id == company_id)
    )
    return [CompanyDocumentResponse.model_validate(doc) for doc in result.scalars().all()]


@router.post("/companies/{company_id}/documents", response_model=CompanyDocumentResponse)
async def create_company_document(
    company_id: str,
    payload: CompanyDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    parent_id = payload.parent_id if hasattr(payload, "parent_id") else None
    if parent_id:
        parent_result = await db.execute(
            select(CompanyDocument).where(CompanyDocument.id == parent_id)
        )
        parent_doc = parent_result.scalar_one_or_none()
        if not parent_doc or parent_doc.company_id != company_id:
            raise HTTPException(status_code=400, detail="Invalid parent document")

    doc = CompanyDocument(
        company_id=company_id,
        doc_type=payload.doc_type,
        doc_value=payload.doc_value,
        file_name=payload.file_name,
        file_url=payload.file_url,
        storage_path=payload.storage_path,
        parent_id=parent_id,
        status=payload.status or "pending",
        comment=payload.comment,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return CompanyDocumentResponse.model_validate(doc)


@router.patch("/documents/{document_id}", response_model=CompanyDocumentResponse)
async def update_company_document(
    document_id: str,
    payload: CompanyDocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompanyDocument).where(CompanyDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = payload.dict(exclude_unset=True)
    if update_data.get("status") == "rejected" and not update_data.get("comment"):
        raise HTTPException(status_code=400, detail="Comment is required for rejection")

    for key, value in update_data.items():
        setattr(doc, key, value)
    await db.commit()
    await db.refresh(doc)
    return CompanyDocumentResponse.model_validate(doc)


@router.delete("/documents/{document_id}")
async def delete_company_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompanyDocument).where(CompanyDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status == "approved":
        raise HTTPException(status_code=400, detail="Approved documents cannot be deleted")
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.post("/companies/{company_id}/documents/upload", response_model=CompanyDocumentResponse)
async def upload_company_document(
    company_id: str,
    doc_type: str = Form(...),
    doc_value: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    if parent_id:
        parent_result = await db.execute(
            select(CompanyDocument).where(CompanyDocument.id == parent_id)
        )
        parent_doc = parent_result.scalar_one_or_none()
        if not parent_doc or parent_doc.company_id != company_id:
            raise HTTPException(status_code=400, detail="Invalid parent document")

    content = await file.read()
    safe_name = clean_name(file.filename or "document")
    base_path = f"{(settings.STORAGE_LOCAL_ROOT or '').rstrip('/')}/accreditations/{company_id}/{doc_type}"
    await ensure_path(base_path)
    storage_path = f"{base_path}/{safe_name}"
    await upload_bytes_with_safe_extension(storage_path, content)

    doc = CompanyDocument(
        company_id=company_id,
        doc_type=doc_type,
        doc_value=doc_value,
        file_name=safe_name,
        storage_path=storage_path,
        parent_id=parent_id,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return CompanyDocumentResponse.model_validate(doc)


@router.get("/documents/{document_id}/download")
async def download_company_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    result = await db.execute(
        select(CompanyDocument).where(CompanyDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_path:
        raise HTTPException(status_code=400, detail="Document does not have storage path")

    href = await get_download_href(doc.storage_path)
    return {"href": href}
