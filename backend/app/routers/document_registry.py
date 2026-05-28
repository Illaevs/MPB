"""
Consolidated document registry API router.
"""
from typing import List, Optional
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.services.permissions import allowed_deal_ids, get_section_permissions
from app.models import (
    Document,
    DocumentRelation,
    DocumentPackage,
    DocumentPackageItem,
    DocumentDispatch,
    DocumentDispatchChannel,
    User,
)
from app.services.event_log import log_event
from app.schemas.document_registry import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentRelationCreate,
    DocumentRelationResponse,
    DocumentPackageCreate,
    DocumentPackageUpdate,
    DocumentPackageResponse,
    DocumentPackageItemCreate,
    DocumentPackageItemResponse,
    DocumentDispatchCreate,
    DocumentDispatchResponse,
    DocumentDispatchChannelCreate,
    DocumentDispatchChannelUpdate,
    DocumentDispatchChannelResponse,
)
from app.services.storage import (
    clean_name,
    ensure_path,
    list_items,
    upload_bytes_with_safe_extension,
    get_download_href,
    delete_path,
    local_path,
    storage_available,
)

router = APIRouter()


def _apply_search(query, search: str):
    tokens = [t.strip() for t in search.split() if t.strip()]
    for token in tokens:
        pattern = f"%{token}%"
        pattern_upper = f"%{token.upper()}%"
        query = query.where(
            or_(
                Document.title.like(pattern), Document.title.like(pattern_upper),
                Document.number.like(pattern), Document.number.like(pattern_upper),
                Document.doc_type.like(pattern), Document.doc_type.like(pattern_upper),
            )
        )
    return query


def _build_registry_root(entity_id: str, title: str) -> str:
    base = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    safe_title = clean_name(title or f"Document {entity_id}")
    return f"{base}/Document Registry/[{entity_id}] {safe_title}"


async def _resolve_dispatch_path(
    db: AsyncSession,
    dispatch: DocumentDispatch,
    channel: str,
) -> str:
    if dispatch.document_id:
        result = await db.execute(select(Document).where(Document.id == dispatch.document_id))
        doc = result.scalar_one_or_none()
        entity_id = str(doc.id) if doc else str(dispatch.document_id)
        title = doc.title if doc else "Document"
    else:
        result = await db.execute(select(DocumentPackage).where(DocumentPackage.id == dispatch.package_id))
        pkg = result.scalar_one_or_none()
        entity_id = str(pkg.id) if pkg else str(dispatch.package_id)
        title = pkg.title if pkg else "Package"
    root = _build_registry_root(entity_id, title)
    return f"{root}/{clean_name(channel)}"


def _validate_channel_file_path(channel_root: str, file_path: str) -> None:
    try:
        root_resolved = local_path(channel_root).resolve(strict=False)
        file_resolved = local_path(file_path).resolve(strict=False)
        file_resolved.relative_to(root_resolved)
        if file_resolved == root_resolved:
            raise ValueError("File path points to channel root")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    project_id: Optional[str] = None,
    counterparty_id: Optional[str] = None,
    our_company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    query = select(Document)
    if search:
        query = _apply_search(query, search)
    if doc_type:
        types = [t.strip() for t in doc_type.split(",") if t.strip()]
        if types:
            query = query.where(Document.doc_type.in_(types))
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if statuses:
            query = query.where(Document.status.in_(statuses))
    if date_from:
        try:
            date_from_value = date_type.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from")
        query = query.where(Document.document_date >= date_from_value)
    if date_to:
        try:
            date_to_value = date_type.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to")
        query = query.where(Document.document_date <= date_to_value)
    if project_id:
        query = query.where(Document.project_id == project_id)
    if counterparty_id:
        query = query.where(Document.counterparty_id == counterparty_id)
    if our_company_id:
        query = query.where(Document.our_company_id == our_company_id)
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "document_registry")
    if not read_all:
        if not read_assigned:
            return []
        allowed = await allowed_deal_ids(db, request, user)
        if allowed == []:
            return []
        query = query.where(Document.project_id.in_(allowed))
    result = await db.execute(query.order_by(Document.document_date.desc(), Document.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=DocumentResponse)
async def create_document(
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    from app.services.our_company import apply_default_our_company
    data = payload.dict()
    await apply_default_our_company(db, data)
    doc = Document(**data)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    try:
        await log_event(
            db,
            entity_type="document",
            entity_id=str(doc.id),
            action="document.create",
            created_by=str(user.id),
            details={
                "document_id": str(doc.id),
                "document_title": doc.title,
                "doc_type": doc.doc_type,
                "status": doc.status,
                "deal_id": doc.project_id,
            },
        )
    except Exception:
        pass
    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    payload: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    previous_status = doc.status
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(doc, key, value)
    await db.commit()
    await db.refresh(doc)
    try:
        await log_event(
            db,
            entity_type="document",
            entity_id=str(doc.id),
            action="document.update",
            created_by=str(user.id),
            details={
                "document_id": str(doc.id),
                "document_title": doc.title,
                "doc_type": doc.doc_type,
                "status": doc.status,
                "deal_id": doc.project_id,
            },
        )
        if previous_status != doc.status and doc.status == "received":
            await log_event(
                db,
                entity_type="document",
                entity_id=str(doc.id),
                action="document.received",
                created_by=str(user.id),
                details={
                    "document_id": str(doc.id),
                    "document_title": doc.title,
                    "doc_type": doc.doc_type,
                    "status": doc.status,
                    "deal_id": doc.project_id,
                },
            )
    except Exception:
        pass
    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


from sqlalchemy.orm import selectinload

@router.get("/{document_id}/relations", response_model=List[DocumentRelationResponse])
async def list_relations(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentRelation)
        .where(DocumentRelation.document_id == document_id)
        .options(
            selectinload(DocumentRelation.related_document),
            selectinload(DocumentRelation.document)
        )
    )
    return result.scalars().all()


@router.get("/{document_id}/parent-relations", response_model=List[DocumentRelationResponse])
async def list_parent_relations(document_id: str, db: AsyncSession = Depends(get_db)):
    """Get relations where this document is the child (linked TO by other documents)"""
    result = await db.execute(
        select(DocumentRelation)
        .where(DocumentRelation.related_document_id == document_id)
        .options(
            selectinload(DocumentRelation.document),
            selectinload(DocumentRelation.related_document)
        )
    )
    return result.scalars().all()


@router.post("/{document_id}/relations", response_model=DocumentRelationResponse)
async def add_relation(document_id: str, payload: DocumentRelationCreate, db: AsyncSession = Depends(get_db)):
    if document_id == payload.related_document_id:
        raise HTTPException(status_code=400, detail="Cannot link document to itself")
    result = await db.execute(select(Document).where(Document.id == document_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document not found")
    related = await db.execute(select(Document).where(Document.id == payload.related_document_id))
    if not related.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Related document not found")
    
    # Check for existing relation
    existing = await db.execute(
        select(DocumentRelation).where(
            DocumentRelation.document_id == document_id,
            DocumentRelation.related_document_id == payload.related_document_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Relation already exists")
    
    rel = DocumentRelation(document_id=document_id, related_document_id=payload.related_document_id, relation_type=payload.relation_type)
    db.add(rel)
    await db.commit()
    result = await db.execute(
        select(DocumentRelation)
        .where(DocumentRelation.id == rel.id)
        .options(
            selectinload(DocumentRelation.related_document),
            selectinload(DocumentRelation.document)
        )
    )
    return result.scalar_one()


@router.delete("/relations/{relation_id}")
async def delete_relation(relation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentRelation).where(DocumentRelation.id == relation_id))
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    await db.delete(rel)
    await db.commit()
    return {"message": "Relation deleted"}


@router.get("/packages", response_model=List[DocumentPackageResponse])
async def list_packages(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    counterparty_id: Optional[str] = None,
    our_company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DocumentPackage)
    if search:
        tokens = [t.strip() for t in search.split() if t.strip()]
        for token in tokens:
            pattern = f"%{token}%"
            pattern_upper = f"%{token.upper()}%"
            query = query.where(
                or_(
                    DocumentPackage.title.like(pattern),
                    DocumentPackage.title.like(pattern_upper),
                )
            )
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if statuses:
            query = query.where(DocumentPackage.status.in_(statuses))
    if project_id:
        query = query.where(DocumentPackage.project_id == project_id)
    if counterparty_id:
        query = query.where(DocumentPackage.counterparty_id == counterparty_id)
    if our_company_id:
        query = query.where(DocumentPackage.our_company_id == our_company_id)
    result = await db.execute(query.order_by(DocumentPackage.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/packages", response_model=DocumentPackageResponse)
async def create_package(payload: DocumentPackageCreate, db: AsyncSession = Depends(get_db)):
    from app.services.our_company import apply_default_our_company
    data = payload.dict()
    await apply_default_our_company(db, data)
    package = DocumentPackage(**data)
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


@router.put("/packages/{package_id}", response_model=DocumentPackageResponse)
async def update_package(package_id: str, payload: DocumentPackageUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPackage).where(DocumentPackage.id == package_id))
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(package, key, value)
    await db.commit()
    await db.refresh(package)
    return package


@router.delete("/packages/{package_id}")
async def delete_package(package_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPackage).where(DocumentPackage.id == package_id))
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    await db.execute(delete(DocumentPackageItem).where(DocumentPackageItem.package_id == package_id))
    await db.delete(package)
    await db.commit()
    return {"message": "Package deleted"}


@router.get("/packages/{package_id}/items", response_model=List[DocumentPackageItemResponse])
async def list_package_items(package_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPackageItem).where(DocumentPackageItem.package_id == package_id))
    return result.scalars().all()


@router.post("/packages/{package_id}/items", response_model=DocumentPackageItemResponse)
async def add_package_item(package_id: str, payload: DocumentPackageItemCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPackage).where(DocumentPackage.id == package_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Package not found")
    doc = await db.execute(select(Document).where(Document.id == payload.document_id))
    if not doc.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document not found")
    item = DocumentPackageItem(package_id=package_id, document_id=payload.document_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/packages/items/{item_id}")
async def delete_package_item(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPackageItem).where(DocumentPackageItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Package item not found")
    await db.delete(item)
    await db.commit()
    return {"message": "Package item deleted"}


@router.get("/dispatches", response_model=List[DocumentDispatchResponse])
async def list_dispatches(
    document_id: Optional[str] = None,
    package_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DocumentDispatch)
    if document_id:
        query = query.where(DocumentDispatch.document_id == document_id)
    if package_id:
        query = query.where(DocumentDispatch.package_id == package_id)
    result = await db.execute(query.order_by(DocumentDispatch.created_at.desc()))
    return result.scalars().all()


@router.post("/dispatches", response_model=DocumentDispatchResponse)
async def create_dispatch(
    payload: DocumentDispatchCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if bool(payload.document_id) == bool(payload.package_id):
        raise HTTPException(status_code=400, detail="Provide either document_id or package_id")
    if payload.document_id:
        doc = await db.execute(select(Document).where(Document.id == payload.document_id))
        if not doc.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Document not found")
    if payload.package_id:
        pkg = await db.execute(select(DocumentPackage).where(DocumentPackage.id == payload.package_id))
        if not pkg.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Package not found")
    dispatch = DocumentDispatch(**payload.dict())
    db.add(dispatch)
    await db.commit()
    await db.refresh(dispatch)
    try:
        doc_title = None
        deal_id = None
        if dispatch.document_id:
            result = await db.execute(select(Document).where(Document.id == dispatch.document_id))
            doc = result.scalar_one_or_none()
            doc_title = doc.title if doc else None
            deal_id = doc.project_id if doc else None
        await log_event(
            db,
            entity_type="document",
            entity_id=str(dispatch.document_id or dispatch.package_id),
            action="document.sent",
            created_by=str(user.id),
            details={
                "document_id": str(dispatch.document_id or ""),
                "package_id": str(dispatch.package_id or ""),
                "document_title": doc_title,
                "deal_id": deal_id,
            },
        )
    except Exception:
        pass
    return dispatch


@router.post("/dispatches/{dispatch_id}/channels", response_model=DocumentDispatchChannelResponse)
async def add_dispatch_channel(
    dispatch_id: str,
    payload: DocumentDispatchChannelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    dispatch_result = await db.execute(select(DocumentDispatch).where(DocumentDispatch.id == dispatch_id))
    dispatch_obj = dispatch_result.scalar_one_or_none()
    if not dispatch_obj:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    channel = DocumentDispatchChannel(dispatch_id=dispatch_id, **payload.dict())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    try:
        document_id = dispatch_obj.document_id if dispatch_obj else None
        doc_title = None
        deal_id = None
        if document_id:
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            doc_title = doc.title if doc else None
            deal_id = doc.project_id if doc else None
        await log_event(
            db,
            entity_type="document",
            entity_id=str(document_id or dispatch_id),
            action="document.sent",
            created_by=str(user.id),
            details={
                "document_id": str(document_id or ""),
                "channel": channel.channel,
                "channel_date": str(channel.channel_date),
                "document_title": doc_title,
                "deal_id": deal_id,
            },
        )
    except Exception:
        pass
    return channel


@router.get("/dispatches/{dispatch_id}/channels", response_model=List[DocumentDispatchChannelResponse])
async def list_dispatch_channels(dispatch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.dispatch_id == dispatch_id))
    return result.scalars().all()


@router.get("/dispatches/{dispatch_id}/channels/{channel_id}/files")
async def list_dispatch_channel_files(
    dispatch_id: str,
    channel_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    if not channel.confirmation_file:
        return []
    return await list_items(channel.confirmation_file)


@router.post("/dispatches/{dispatch_id}/channels/{channel_id}/upload")
async def upload_dispatch_channel_files(
    dispatch_id: str,
    channel_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    if not files:
        raise HTTPException(status_code=400, detail="Files are required")
    dispatch_result = await db.execute(select(DocumentDispatch).where(DocumentDispatch.id == dispatch_id))
    dispatch = dispatch_result.scalar_one_or_none()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    channel_result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = channel_result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    target_path = channel.confirmation_file or await _resolve_dispatch_path(db, dispatch, channel.channel)
    await ensure_path(target_path)
    uploaded = 0
    for upload in files:
        content = await upload.read()
        file_path = f"{target_path.rstrip('/')}/{clean_name(upload.filename)}"
        await upload_bytes_with_safe_extension(file_path, content)
        uploaded += 1
    if channel.confirmation_file != target_path:
        channel.confirmation_file = target_path
        await db.commit()
        await db.refresh(channel)
    return {"uploaded": uploaded, "path": target_path}


@router.get("/dispatches/{dispatch_id}/channels/{channel_id}/download")
async def download_dispatch_channel_file(
    dispatch_id: str,
    channel_id: str,
    file_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    if not channel.confirmation_file:
        raise HTTPException(status_code=404, detail="Files not found")
    _validate_channel_file_path(channel.confirmation_file, file_path)
    href = await get_download_href(file_path)
    return {"href": href}


@router.delete("/dispatches/{dispatch_id}/channels/{channel_id}/files")
async def delete_dispatch_channel_file(
    dispatch_id: str,
    channel_id: str,
    file_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    if not channel.confirmation_file:
        raise HTTPException(status_code=404, detail="Files not found")
    _validate_channel_file_path(channel.confirmation_file, file_path)
    await delete_path(file_path)
    return {"message": "File deleted"}


@router.put("/dispatches/{dispatch_id}/channels/{channel_id}", response_model=DocumentDispatchChannelResponse)
async def update_dispatch_channel(
    dispatch_id: str,
    channel_id: str,
    payload: DocumentDispatchChannelUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(channel, key, value)
    await db.commit()
    await db.refresh(channel)
    try:
        await log_event(
            db,
            entity_type="document",
            entity_id=str(channel.dispatch_id),
            action="document.update",
            created_by=str(user.id),
            details={
                "dispatch_id": str(channel.dispatch_id),
                "channel_id": str(channel.id),
                "channel": channel.channel,
                "channel_date": str(channel.channel_date),
            },
        )
    except Exception:
        pass
    return channel


@router.delete("/dispatches/{dispatch_id}/channels/{channel_id}")
async def delete_dispatch_channel(dispatch_id: str, channel_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentDispatchChannel).where(DocumentDispatchChannel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel or channel.dispatch_id != dispatch_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(channel)
    await db.commit()
    return {"message": "Channel deleted"}


@router.delete("/dispatches/{dispatch_id}")
async def delete_dispatch(dispatch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentDispatch).where(DocumentDispatch.id == dispatch_id))
    dispatch = result.scalar_one_or_none()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    await db.delete(dispatch)
    await db.commit()
    return {"message": "Dispatch deleted"}


# IMPORTANT: This route must be LAST as it catches all /{document_id} patterns
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "document_registry")
    if not read_all:
        if not read_assigned:
            raise HTTPException(status_code=404, detail="Document not found")
        allowed = await allowed_deal_ids(db, request, user)
        if allowed is not None:
            if not doc.project_id or str(doc.project_id) not in set(allowed):
                raise HTTPException(status_code=404, detail="Document not found")
    return doc
