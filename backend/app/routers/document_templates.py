"""
Document templates API.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import DocumentTemplate, DocumentTemplateVersion
from app.services.document_template_fields import (
    extract_docx_placeholders,
    get_template_field_groups,
    get_template_fields,
    unknown_placeholder_keys,
)
from app.services.permissions import require_section_read, require_section_write
from app.services.storage import clean_name, read_file_bytes, storage_available, upload_bytes_with_safe_extension


router = APIRouter()

ALLOWED_TEMPLATE_EXTENSIONS = {".docx"}
MODULE_OPTIONS = [
    {"value": "outgoing_registry", "label": "Исходящие"},
    {"value": "contracts", "label": "Договоры"},
    {"value": "document_registry", "label": "Документация"},
]
DOCUMENT_KIND_OPTIONS = [
    {"value": "letter", "label": "Письмо", "module": "outgoing_registry"},
    {"value": "invoice", "label": "Счет", "module": "outgoing_registry"},
    {"value": "upd", "label": "УПД", "module": "outgoing_registry"},
    {"value": "act", "label": "Акт", "module": "outgoing_registry"},
    {"value": "vat_invoice", "label": "Счет-фактура", "module": "outgoing_registry"},
    {"value": "contract", "label": "Договор", "module": "contracts"},
    {"value": "additional_agreement", "label": "Доп. соглашение", "module": "contracts"},
    {"value": "contract_act", "label": "Акт по договору", "module": "contracts"},
]
STATUS_OPTIONS = [
    {"value": "draft", "label": "Черновик"},
    {"value": "approved", "label": "Утвержден"},
    {"value": "archived", "label": "Архив"},
]
BINDING_OPTIONS = [
    {"value": "global", "label": "Глобальный"},
    {"value": "module", "label": "По модулю"},
    {"value": "company", "label": "По нашей компании"},
    {"value": "counterparty", "label": "По контрагенту"},
    {"value": "deal", "label": "По сделке"},
    {"value": "contract", "label": "По договору"},
]


def _normalize_option(value: Optional[str], allowed: set[str], default: str) -> str:
    normalized = (value or "").strip()
    return normalized if normalized in allowed else default


def _normalize_binding_id(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    return text or None


def _validate_template_file(file_name: str, content: bytes) -> None:
    suffix = Path(file_name or "").suffix.lower()
    if suffix not in ALLOWED_TEMPLATE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Поддерживаются только шаблоны .docx")
    if not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Файл не похож на корректный DOCX")


def _template_storage_path(template_id: str, version_number: int, file_name: str) -> str:
    safe_name = clean_name(file_name or "template.docx")
    return f"{settings.STORAGE_LOCAL_ROOT.rstrip('/')}/document-templates/{template_id}/v{version_number}/{safe_name}"


async def _next_version_number(db: AsyncSession, template_id: str) -> int:
    result = await db.execute(
        select(func.max(DocumentTemplateVersion.version_number)).where(
            DocumentTemplateVersion.template_id == str(template_id)
        )
    )
    return int(result.scalar() or 0) + 1


async def _deactivate_same_scope(db: AsyncSession, template: DocumentTemplate) -> None:
    filters = [
        DocumentTemplate.id != str(template.id),
        DocumentTemplate.module == template.module,
        DocumentTemplate.document_kind == template.document_kind,
        DocumentTemplate.binding_type == template.binding_type,
        DocumentTemplate.is_active == True,  # noqa: E712
    ]
    filters.append(
        DocumentTemplate.binding_id.is_(None)
        if template.binding_id is None
        else DocumentTemplate.binding_id == template.binding_id
    )
    filters.append(
        DocumentTemplate.our_company_key.is_(None)
        if template.our_company_key is None
        else DocumentTemplate.our_company_key == template.our_company_key
    )
    result = await db.execute(select(DocumentTemplate).where(and_(*filters)))
    for item in result.scalars().all():
        item.is_active = False


async def _create_version(
    db: AsyncSession,
    *,
    template: DocumentTemplate,
    upload: UploadFile,
    user_id: str,
) -> DocumentTemplateVersion:
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    content = await upload.read()
    _validate_template_file(upload.filename or "", content)
    placeholders = extract_docx_placeholders(content)
    unknown_fields = unknown_placeholder_keys(placeholders)
    version_number = await _next_version_number(db, str(template.id))
    file_name = clean_name(upload.filename or "template.docx")
    file_path = _template_storage_path(str(template.id), version_number, file_name)
    await upload_bytes_with_safe_extension(file_path, content)
    version = DocumentTemplateVersion(
        template_id=str(template.id),
        version_number=version_number,
        file_name=file_name,
        file_path=file_path,
        file_size=len(content),
        content_type=upload.content_type or mimetypes.guess_type(file_name)[0],
        fields_json=placeholders,
        unknown_fields_json=unknown_fields,
        created_by=str(user_id),
    )
    db.add(version)
    await db.flush()
    template.current_version_id = str(version.id)
    template.fields_json = placeholders
    template.unknown_fields_json = unknown_fields
    template.updated_by = str(user_id)
    return version


async def _latest_version(db: AsyncSession, template_id: str) -> Optional[DocumentTemplateVersion]:
    result = await db.execute(
        select(DocumentTemplateVersion)
        .where(DocumentTemplateVersion.template_id == str(template_id))
        .order_by(DocumentTemplateVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _serialize_template(db: AsyncSession, template: DocumentTemplate, include_versions: bool = False) -> dict:
    current_version = None
    if template.current_version_id:
        result = await db.execute(
            select(DocumentTemplateVersion).where(DocumentTemplateVersion.id == str(template.current_version_id))
        )
        current_version = result.scalar_one_or_none()
    if not current_version:
        current_version = await _latest_version(db, str(template.id))
    payload = {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "module": template.module,
        "document_kind": template.document_kind,
        "our_company_key": template.our_company_key,
        "binding_type": template.binding_type,
        "binding_id": template.binding_id,
        "status": template.status,
        "is_active": bool(template.is_active),
        "current_version_id": str(current_version.id) if current_version else None,
        "current_version_number": current_version.version_number if current_version else None,
        "file_name": current_version.file_name if current_version else None,
        "file_size": current_version.file_size if current_version else None,
        "fields": template.fields_json or [],
        "unknown_fields": template.unknown_fields_json or [],
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }
    if include_versions:
        result = await db.execute(
            select(DocumentTemplateVersion)
            .where(DocumentTemplateVersion.template_id == str(template.id))
            .order_by(DocumentTemplateVersion.version_number.desc())
        )
        payload["versions"] = [
            {
                "id": str(version.id),
                "version_number": version.version_number,
                "file_name": version.file_name,
                "file_size": version.file_size,
                "content_type": version.content_type,
                "fields": version.fields_json or [],
                "unknown_fields": version.unknown_fields_json or [],
                "created_at": version.created_at,
                "created_by": version.created_by,
            }
            for version in result.scalars().all()
        ]
    return payload


@router.get("/meta")
async def get_template_meta(_=Depends(require_section_read("document_templates"))):
    return {
        "modules": MODULE_OPTIONS,
        "document_kinds": DOCUMENT_KIND_OPTIONS,
        "statuses": STATUS_OPTIONS,
        "bindings": BINDING_OPTIONS,
    }


@router.get("/fields")
async def list_template_fields(
    search: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    document_kind: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    _=Depends(require_section_read("document_templates")),
):
    return get_template_fields(search=search, module=module, document_kind=document_kind, group=group)


@router.get("/field-groups")
async def list_template_field_groups(_=Depends(require_section_read("document_templates"))):
    return get_template_field_groups()


@router.get("/")
async def list_templates(
    search: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    document_kind: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("document_templates")),
):
    query = select(DocumentTemplate)
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                DocumentTemplate.name.ilike(term),
                DocumentTemplate.description.ilike(term),
                DocumentTemplate.module.ilike(term),
                DocumentTemplate.document_kind.ilike(term),
            )
        )
    if module:
        filters.append(DocumentTemplate.module == module)
    if document_kind:
        filters.append(DocumentTemplate.document_kind == document_kind)
    if status:
        filters.append(DocumentTemplate.status == status)
    if active is not None:
        filters.append(DocumentTemplate.is_active == active)
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(DocumentTemplate.updated_at.desc(), DocumentTemplate.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [await _serialize_template(db, item) for item in result.scalars().all()]


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("document_templates")),
):
    template = await db.get(DocumentTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return await _serialize_template(db, template, include_versions=True)


@router.post("/")
async def create_template(
    name: str = Form(...),
    module: str = Form("outgoing_registry"),
    document_kind: str = Form("letter"),
    status: str = Form("draft"),
    is_active: bool = Form(False),
    description: Optional[str] = Form(None),
    our_company_key: Optional[str] = Form(None),
    binding_type: str = Form("global"),
    binding_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("document_templates")),
):
    allowed_modules = {item["value"] for item in MODULE_OPTIONS}
    allowed_kinds = {item["value"] for item in DOCUMENT_KIND_OPTIONS}
    allowed_statuses = {item["value"] for item in STATUS_OPTIONS}
    allowed_bindings = {item["value"] for item in BINDING_OPTIONS}
    template = DocumentTemplate(
        name=name.strip(),
        description=(description or "").strip() or None,
        module=_normalize_option(module, allowed_modules, "outgoing_registry"),
        document_kind=_normalize_option(document_kind, allowed_kinds, "letter"),
        status=_normalize_option(status, allowed_statuses, "draft"),
        is_active=bool(is_active),
        our_company_key=(our_company_key or "").strip() or None,
        binding_type=_normalize_option(binding_type, allowed_bindings, "global"),
        binding_id=_normalize_binding_id(binding_id),
        created_by=str(user.id),
        updated_by=str(user.id),
    )
    db.add(template)
    await db.flush()
    await _create_version(db, template=template, upload=file, user_id=str(user.id))
    if template.is_active:
        await _deactivate_same_scope(db, template)
    await db.commit()
    await db.refresh(template)
    return await _serialize_template(db, template, include_versions=True)


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("document_templates")),
):
    template = await db.get(DocumentTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    allowed_modules = {item["value"] for item in MODULE_OPTIONS}
    allowed_kinds = {item["value"] for item in DOCUMENT_KIND_OPTIONS}
    allowed_statuses = {item["value"] for item in STATUS_OPTIONS}
    allowed_bindings = {item["value"] for item in BINDING_OPTIONS}
    for field in ("name", "description", "our_company_key", "binding_id"):
        if field in payload:
            value = payload.get(field)
            setattr(template, field, (str(value).strip() if value is not None else None) or None)
    if "module" in payload:
        template.module = _normalize_option(payload.get("module"), allowed_modules, "outgoing_registry")
    if "document_kind" in payload:
        template.document_kind = _normalize_option(payload.get("document_kind"), allowed_kinds, "letter")
    if "binding_type" in payload:
        template.binding_type = _normalize_option(payload.get("binding_type"), allowed_bindings, "global")
    if "status" in payload:
        template.status = _normalize_option(payload.get("status"), allowed_statuses, "draft")
    if "is_active" in payload:
        template.is_active = bool(payload.get("is_active"))
    template.updated_by = str(user.id)
    if template.is_active:
        await _deactivate_same_scope(db, template)
    await db.commit()
    await db.refresh(template)
    return await _serialize_template(db, template, include_versions=True)


@router.post("/{template_id}/versions")
async def upload_template_version(
    template_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
    _=Depends(require_section_write("document_templates")),
):
    template = await db.get(DocumentTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await _create_version(db, template=template, upload=file, user_id=str(user.id))
    if template.is_active:
        await _deactivate_same_scope(db, template)
    await db.commit()
    await db.refresh(template)
    return await _serialize_template(db, template, include_versions=True)


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("document_templates")),
):
    template = await db.get(DocumentTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
    await db.commit()
    return {"ok": True}


@router.get("/{template_id}/download")
async def download_template(
    template_id: str,
    version_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("document_templates")),
):
    template = await db.get(DocumentTemplate, str(template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if version_id:
        result = await db.execute(
            select(DocumentTemplateVersion).where(
                and_(
                    DocumentTemplateVersion.id == str(version_id),
                    DocumentTemplateVersion.template_id == str(template.id),
                )
            )
        )
        version = result.scalar_one_or_none()
    else:
        version = await _latest_version(db, str(template.id))
    if not version:
        raise HTTPException(status_code=404, detail="Template version not found")
    try:
        content = await read_file_bytes(version.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template file not found")
    filename = version.file_name or "template.docx"
    quoted = quote(filename)
    return Response(
        content,
        media_type=version.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quoted}",
            "Cache-Control": "no-store",
        },
    )
