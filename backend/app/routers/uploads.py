"""
Upload queue endpoints (async uploads to storage).
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import (
    Contract,
    ContractDocument,
    ContractDocumentProductLink,
    DealProduct,
    DocumentDispatch,
    DocumentDispatchChannel,
    UploadJob,
    User,
    CompanyDocument,
    LegalCaseEvent,
    LegalCase,
    OutgoingDocument,
    StageResult,
    SubcontractorCard,
    Deal,
    Lead,
    LeadProduct,
    KpDocument,
    KpVersion,
)
from app.schemas.upload_job import UploadJobResponse
from app.services.storage import clean_name, is_local_storage, upload_file_with_safe_extension_sync
from app.services.upload_security import write_upload_to_tmp as secure_write_upload_to_tmp
from app.services.sequence_lock import sequence_lock
from app.utils.num2words_ru import num2text_rur
from app.routers.contracts import ALLOWED_DOC_TYPES, ALLOWED_DOC_STATUSES, ALLOWED_FILE_KINDS
from app.routers.document_registry import _resolve_dispatch_path
from app.routers.executor import _build_root_paths, _find_matching_deal

router = APIRouter()


def _document_amount(value: Optional[float]) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid amount")
    if amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    return amount


def _parse_product_ids(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    text = str(raw).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        source = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        source = text.split(",")
    result = []
    seen = set()
    for value in source:
        item = str(value or "").strip()
        if not item:
            continue
        key = item.replace("-", "").lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _normalize_link_key(value: Optional[str]) -> str:
    return str(value or "").replace("-", "").lower()


async def _set_invoice_product_links(db: AsyncSession, document: ContractDocument, deal_product_ids: List[str]) -> None:
    await db.execute(
        delete(ContractDocumentProductLink)
        .where(ContractDocumentProductLink.contract_document_id == str(document.id))
    )
    if document.doc_type != "invoice" or not deal_product_ids:
        await db.commit()
        return

    contract = await Contract.get_by_id(db, str(document.contract_id))
    if not contract or not contract.deal_id:
        raise HTTPException(status_code=400, detail="Invoice product links require contract deal")

    deal_products = await DealProduct.get_by_deal(db, str(contract.deal_id))
    available = {_normalize_link_key(item.id): str(item.id) for item in deal_products}
    for requested_id in deal_product_ids:
        real_id = available.get(_normalize_link_key(requested_id))
        if not real_id:
            raise HTTPException(status_code=400, detail="Deal product does not belong to contract deal")
        db.add(ContractDocumentProductLink(
            contract_document_id=str(document.id),
            deal_product_id=real_id,
        ))
    await db.commit()

BLOCKED_UPLOAD_EXTENSIONS = {
    ".apk",
    ".appimage",
    ".bat",
    ".cmd",
    ".com",
    ".cpl",
    ".dll",
    ".exe",
    ".hta",
    ".html",
    ".htm",
    ".jar",
    ".js",
    ".lnk",
    ".mjs",
    ".msi",
    ".php",
    ".phar",
    ".phtml",
    ".pl",
    ".ps1",
    ".py",
    ".rb",
    ".scr",
    ".sh",
    ".svg",
    ".svgz",
    ".vbe",
    ".vbs",
    ".wsf",
    ".xhtml",
}

ALLOWED_UPLOAD_EXTENSIONS = {
    ".7z",
    ".bmp",
    ".csv",
    ".doc",
    ".docx",
    ".dwg",
    ".dxf",
    ".eml",
    ".gif",
    ".jpeg",
    ".jpg",
    ".msg",
    ".ods",
    ".odt",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".rtf",
    ".sig",
    ".txt",
    ".tif",
    ".tiff",
    ".webp",
    ".xls",
    ".xlsx",
    ".xml",
    ".zip",
}

BLOCKED_CONTENT_TYPES = {
    "application/javascript",
    "application/x-bat",
    "application/x-dosexec",
    "application/x-httpd-php",
    "application/x-msdos-program",
    "application/x-msdownload",
    "application/x-sh",
    "image/svg+xml",
    "text/html",
}


def _tmp_dir() -> Path:
    if settings.UPLOAD_TMP_DIR:
        return Path(settings.UPLOAD_TMP_DIR)
    base = Path(__file__).resolve().parents[3]
    return base / "tmp_uploads"


def _id_conditions(column, value):
    variants = []
    try:
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        variants.extend([parsed, str(parsed), parsed.hex])
    except (ValueError, TypeError):
        variants.append(str(value))
    return or_(*[column == v for v in variants])


def _upload_tmp_max_bytes() -> int:
    return settings.UPLOAD_TMP_MAX_BYTES or 256 * 1024 * 1024


async def _write_upload_to_tmp(upload: UploadFile, max_bytes: int) -> tuple[str, int]:
    return await secure_write_upload_to_tmp(upload, max_bytes)
    tmp_dir = _tmp_dir()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    safe_name = clean_name(upload.filename or "upload")
    suffix = Path(safe_name).suffix.lower()
    content_type = (upload.content_type or "").lower()
    if suffix in BLOCKED_UPLOAD_EXTENSIONS or content_type in BLOCKED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Этот тип файла запрещен к загрузке.")
    if suffix and suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла.")
    temp_name = f"{uuid.uuid4()}_{safe_name}"
    temp_path = tmp_dir / temp_name

    size_bytes = 0
    with open(temp_path, "wb") as out_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            if size_bytes > max_bytes:
                out_file.close()
                temp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File is too large")
            out_file.write(chunk)

    return str(temp_path), size_bytes


@router.get("/", response_model=List[UploadJobResponse])
async def list_upload_jobs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    query = select(UploadJob).where(UploadJob.created_by == str(user.id)).order_by(UploadJob.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/contracts/documents", response_model=UploadJobResponse)
async def queue_contract_document_upload(
    contract_id: str = Form(...),
    doc_type: Optional[str] = Form(None),
    status: Optional[str] = Form("draft"),
    document_id: Optional[str] = Form(None),
    file_kind: str = Form(...),
    amount: Optional[float] = Form(None),
    product_ids: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if file_kind not in ALLOWED_FILE_KINDS:
        raise HTTPException(status_code=400, detail="Invalid file_kind")
    if status and status not in ALLOWED_DOC_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    contract = await Contract.get_by_id(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if document_id:
        document = await ContractDocument.get_by_id(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        if str(document.contract_id) not in {contract_id, contract_id.replace("-", "")}:
            raise HTTPException(status_code=400, detail="Document does not belong to contract")
        doc_type = document.doc_type
        number_in_contract = document.number_in_contract
    else:
        if not doc_type or doc_type not in ALLOWED_DOC_TYPES:
            raise HTTPException(status_code=400, detail="Invalid doc_type")
        # Serialize MAX(number_in_contract)+1 -> INSERT (no UNIQUE
        # constraint; a race silently duplicates the document number).
        async with sequence_lock("contract_document_number"):
            documents = await ContractDocument.get_by_contract_and_type(db, contract_id, doc_type)
            next_number = (max((d.number_in_contract for d in documents), default=0) + 1) if documents else 1
            document = await ContractDocument.create(
                db,
                contract_id=contract.id,
                doc_type=doc_type,
                number_in_contract=next_number,
                status=status or "draft",
                amount=_document_amount(amount) if doc_type in {"contract", "addendum", "act"} else None,
            )
        await _set_invoice_product_links(db, document, _parse_product_ids(product_ids))
        number_in_contract = next_number

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    safe_name = clean_name(file.filename or f"{doc_type}_{number_in_contract}")
    base_path = f"{settings.STORAGE_LOCAL_ROOT.rstrip('/')}/contracts/{contract_id}/{doc_type}"
    target_path = f"{base_path}/{doc_type}_{number_in_contract}_{file_kind}_{safe_name}"

    if is_local_storage():
        try:
            await asyncio.to_thread(upload_file_with_safe_extension_sync, target_path, temp_path)
        except Exception:
            raise HTTPException(status_code=500, detail="Upload failed")
        update_payload = {}
        if file_kind == "pdf":
            update_payload["pdf_file_name"] = file.filename
            update_payload["pdf_storage_path"] = target_path
        else:
            update_payload["edit_file_name"] = file.filename
            update_payload["edit_storage_path"] = target_path
        await ContractDocument.update(db, str(document.id), **update_payload)
        Path(temp_path).unlink(missing_ok=True)

        job = UploadJob(
            status="done",
            module="contracts",
            entity_id=str(contract_id),
            file_kind=file_kind,
            file_name=file.filename,
            temp_path=temp_path,
            target_path=target_path,
            size_bytes=size_bytes,
            created_by=str(user.id),
            meta={
                "document_id": str(document.id),
                "contract_id": str(contract_id),
                "doc_type": doc_type,
                "number_in_contract": number_in_contract,
                "file_kind": file_kind,
            },
            updated_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    job = UploadJob(
        status="queued",
        module="contracts",
        entity_id=str(contract_id),
        file_kind=file_kind,
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "document_id": str(document.id),
            "contract_id": str(contract_id),
            "doc_type": doc_type,
            "number_in_contract": number_in_contract,
            "file_kind": file_kind,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/document-registry/dispatches/{dispatch_id}/channels/{channel_id}", response_model=UploadJobResponse)
async def queue_document_registry_channel_upload(
    dispatch_id: str,
    channel_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    dispatch_result = await db.execute(select(DocumentDispatch).where(DocumentDispatch.id == dispatch_id))
    dispatch = dispatch_result.scalar_one_or_none()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    channel_result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = channel_result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    channel_folder = channel.confirmation_file or await _resolve_dispatch_path(db, dispatch, channel.channel)
    safe_name = clean_name(file.filename or "file")
    target_path = f"{channel_folder.rstrip('/')}/{safe_name}"

    job = UploadJob(
        status="queued",
        module="document_registry",
        entity_id=str(dispatch_id),
        file_kind="confirmation",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "dispatch_id": str(dispatch_id),
            "channel_id": str(channel_id),
            "channel_folder": channel_folder,
            "file_kind": "confirmation",
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/accreditations/documents", response_model=UploadJobResponse)
async def queue_accreditation_document_upload(
    company_id: str = Form(...),
    doc_type: str = Form(...),
    doc_value: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if parent_id:
        parent_result = await db.execute(select(CompanyDocument).where(CompanyDocument.id == parent_id))
        parent_doc = parent_result.scalar_one_or_none()
        if not parent_doc or str(parent_doc.company_id) not in {company_id, company_id.replace("-", "")}:
            raise HTTPException(status_code=400, detail="Invalid parent document")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    safe_name = clean_name(file.filename or "document")
    base_path = f"{settings.STORAGE_LOCAL_ROOT.rstrip('/')}/accreditations/{company_id}/{doc_type}"
    target_path = f"{base_path}/{safe_name}"

    job = UploadJob(
        status="queued",
        module="accreditations",
        entity_id=str(company_id),
        file_kind="document",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "company_id": str(company_id),
            "doc_type": doc_type,
            "doc_value": doc_value,
            "parent_id": parent_id,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/legal-work/events/{event_id}", response_model=UploadJobResponse)
async def queue_legal_event_file_upload(
    event_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    event = await LegalCaseEvent.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    case = await LegalCase.get_by_id(db, event.legal_case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    safe_name = clean_name(file.filename or "file")
    base_root = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    case_label = clean_name(" - ".join([p for p in [case.case_number, str(case.id)] if p]) or str(case.id))
    base_path = f"{base_root}/Юридическая хронология/{case_label}/events/{event.id}"
    target_path = f"{base_path}/{safe_name}"

    job = UploadJob(
        status="queued",
        module="legal_work",
        entity_id=str(event.legal_case_id),
        file_kind="event_file",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "event_id": str(event.id),
            "file_name": safe_name,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/outgoing-registry/{document_id}/attachments", response_model=UploadJobResponse)
async def queue_outgoing_attachment_upload(
    document_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    document = await OutgoingDocument.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    safe_name = clean_name(file.filename or "attachment")
    base_path = f"{settings.STORAGE_LOCAL_ROOT.rstrip('/')}/Outgoing/{clean_name(document.outgoing_number)}/Attachments"
    target_path = f"{base_path}/{safe_name}"

    job = UploadJob(
        status="queued",
        module="outgoing_registry",
        entity_id=str(document_id),
        file_kind="attachment",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "document_id": str(document_id),
            "file_name": safe_name,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/executor/storage", response_model=UploadJobResponse)
async def queue_executor_folder_upload(
    path: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)
    safe_name = clean_name(file.filename or "file")
    target_path = f"{path.rstrip('/')}/{safe_name}"

    job = UploadJob(
        status="queued",
        module="executor_storage",
        entity_id=str(path),
        file_kind="file",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/executor/results", response_model=List[UploadJobResponse])
async def queue_executor_results_upload(
    stage_id: str = Form(...),
    product_name: str = Form(...),
    subcontractor_card_id: str = Form(...),
    deal_id: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
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
    entity_id = str(deal.id) if deal else str(card.id)
    root_paths = _build_root_paths(entity_id, title_source)
    results_root = root_paths["results"]

    product_folder = f"{results_root}/{clean_name(product_name)}"

    # Serialize MAX(version_number)+1 -> INSERT per (stage, card,
    # product); version_number has no UNIQUE constraint so a race would
    # silently produce two "Версия N" for the same result.
    async with sequence_lock("stage_result_version"):
        version_query = select(func.max(StageResult.version_number)).where(
            _id_conditions(StageResult.stage_id, stage_id),
            _id_conditions(StageResult.subcontractor_card_id, subcontractor_card_id),
            StageResult.product_name == product_name,
        )
        version_result = await db.execute(version_query)
        version_num = int(version_result.scalar() or 0) + 1

        version_label = f"Версия {version_num}"
        version_path = f"{product_folder}/{clean_name(version_label)}"

        result = await StageResult.create(
            db,
            stage_id=stage_id,
            subcontractor_card_id=subcontractor_card_id,
            deal_id=deal.id if deal else None,
            product_name=product_name,
            version_label=version_label,
            version_number=version_num,
            comment=comment,
            storage_path=version_path,
            public_url=None,
            created_by=created_by or getattr(user, "full_name", None) or user.email or str(user.id),
            status="review",
            updated_at=datetime.now(),
        )

    jobs: List[UploadJob] = []
    max_bytes = _upload_tmp_max_bytes()
    for upload in files:
        temp_path, size_bytes = await _write_upload_to_tmp(upload, max_bytes)
        safe_name = clean_name(upload.filename or "file")
        target_path = f"{version_path}/{safe_name}"
        job = UploadJob(
            status="queued",
            module="executor_results",
            entity_id=str(stage_id),
            file_kind="result_file",
            file_name=upload.filename,
            temp_path=temp_path,
            target_path=target_path,
            size_bytes=size_bytes,
            created_by=str(user.id),
            meta={
                "stage_result_id": str(result.id),
                "version_path": version_path,
            },
        )
        db.add(job)
        jobs.append(job)

    await db.commit()
    for job in jobs:
        await db.refresh(job)
    return jobs


@router.post("/kp/versions", response_model=UploadJobResponse)
async def queue_kp_version_upload(
    kp_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    kp = await db.get(KpDocument, kp_id)
    if not kp:
        raise HTTPException(status_code=404, detail="KP not found")

    max_bytes = _upload_tmp_max_bytes()
    temp_path, size_bytes = await _write_upload_to_tmp(file, max_bytes)

    safe_name = clean_name(file.filename or "kp_file")
    base = settings.STORAGE_LOCAL_ROOT.rstrip("/")
    root = f"{base}/KP/{clean_name(kp.number_display)}"
    target_path = f"{root}/{safe_name}"

    lead = await db.get(Lead, kp.lead_id)
    vat_rate = getattr(lead, "vat_rate", 0.0) if lead else 0.0
    products = await LeadProduct.get_by_lead(db, kp.lead_id)
    total = sum(p.final_price or 0 for p in products)
    vat_amount = total * (vat_rate / 100.0)

    version_num = (kp.current_version or 0) + 1
    is_pdf = (file.filename or "").lower().endswith(".pdf")

    version = KpVersion(
        kp_id=kp.id,
        version=version_num,
        docx_url=None,
        pdf_url=None,
        template_id=kp.template_id,
        total_amount=total,
        vat_amount=vat_amount,
        total_text=num2text_rur(total),
        vat_text=num2text_rur(vat_amount),
    )
    db.add(version)
    await db.flush()
    kp.current_version = version_num
    kp.updated_at = datetime.now()

    job = UploadJob(
        status="queued",
        module="kp",
        entity_id=str(kp_id),
        file_kind="kp_version",
        file_name=file.filename,
        temp_path=temp_path,
        target_path=target_path,
        size_bytes=size_bytes,
        created_by=str(user.id),
        meta={
            "kp_id": str(kp.id),
            "version_id": str(version.id),
            "is_pdf": is_pdf,
        },
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
