"""
Files catalog (storage) API Router.
"""
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.services.permissions import get_section_permissions
from app.services.storage import (
    list_items,
    search_items,
    ensure_path,
    clean_name,
    upload_bytes_with_safe_extension,
    upload_file_with_safe_extension,
    is_local_storage,
    local_path,
    delete_path,
    move_path,
    get_download_href,
    storage_available,
)
from app.services.upload_security import (
    validate_upload_metadata,
    write_upload_to_tmp as secure_write_upload_to_tmp,
)


router = APIRouter()


class CreateFolderPayload(BaseModel):
    path: str
    name: str


class RenamePayload(BaseModel):
    path: str
    name: str


class MovePayload(BaseModel):
    from_path: str
    to_path: str


def _strip_disk_prefix(path: str) -> str:
    if path.startswith("disk:"):
        return path[5:]
    return path


def _normalize_path(path: Optional[str]) -> str:
    root = settings.STORAGE_LOCAL_ROOT or "/"
    if not path:
        return root
    return path


def _ensure_within_root(path: str) -> None:
    root = settings.STORAGE_LOCAL_ROOT or "/"
    root_norm = _strip_disk_prefix(root).rstrip("/") or "/"
    path_norm = _strip_disk_prefix(path).rstrip("/") or "/"
    if root_norm == "/":
        return
    if path_norm == root_norm or path_norm.startswith(root_norm + "/"):
        return
    raise HTTPException(status_code=403, detail="Path outside root")


def _is_root_path(path: str) -> bool:
    root = settings.STORAGE_LOCAL_ROOT or "/"
    root_norm = _strip_disk_prefix(root).rstrip("/") or "/"
    path_norm = _strip_disk_prefix(path).rstrip("/") or "/"
    return path_norm == root_norm


def _with_root_prefix(path: str, root: str) -> str:
    if path.startswith("disk:") and not root.startswith("disk:"):
        return f"disk:{root}"
    if root.startswith("disk:") and not path.startswith("disk:"):
        return root[5:]
    return root


def _split_path(path: str) -> tuple:
    if path.startswith("disk:"):
        return "disk:", path[5:]
    return "", path


def _tmp_dir() -> Path:
    if settings.UPLOAD_TMP_DIR:
        return Path(settings.UPLOAD_TMP_DIR)
    base = Path(__file__).resolve().parents[3]
    return base / "tmp_uploads"


async def _write_upload_to_tmp(upload: UploadFile, max_bytes: int) -> tuple[str, int]:
    return await secure_write_upload_to_tmp(upload, max_bytes)
    tmp_dir = _tmp_dir()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    safe_name = clean_name(upload.filename or "upload")
    temp_name = f"{uuid.uuid4()}_{safe_name}"
    temp_path = tmp_dir / temp_name

    size_bytes = 0
    with open(temp_path, "wb") as out_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            if max_bytes and size_bytes > max_bytes:
                out_file.close()
                temp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File is too large")
            out_file.write(chunk)

    return str(temp_path), size_bytes


async def _check_access(db: AsyncSession, user, request: Request) -> None:
    if getattr(request.state, "is_superuser", False):
        return
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "files_catalog")
    if not read_all and not read_assigned:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/files-catalog/list")
async def list_catalog_items(
    request: Request,
    path: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    path = _normalize_path(path)
    _ensure_within_root(path)

    root = _normalize_path(None)
    root = _with_root_prefix(path, root)

    if search:
        items = await search_items(search, path=path, limit=limit)
    else:
        items = await list_items(path, limit=limit)
    items.sort(key=lambda item: (0 if item.get("type") == "folder" else 1, item.get("name") or ""))
    return {"root": root, "path": path, "items": items}


@router.post("/files-catalog/mkdir")
async def create_catalog_folder(
    payload: CreateFolderPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    parent = _normalize_path(payload.path)
    _ensure_within_root(parent)
    name = clean_name(payload.name or "")
    if not name:
        raise HTTPException(status_code=400, detail="Folder name is required")
    folder_path = f"{parent.rstrip('/')}/{name}"
    _ensure_within_root(folder_path)
    await ensure_path(folder_path)
    return {"path": folder_path}


@router.post("/files-catalog/rename")
async def rename_catalog_item(
    payload: RenamePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    source_path = _normalize_path(payload.path)
    _ensure_within_root(source_path)
    name = clean_name(payload.name or "")
    if not name:
        raise HTTPException(status_code=400, detail="New name is required")

    prefix, rest = _split_path(source_path)
    rest = rest.rstrip("/")
    if not rest or rest == _strip_disk_prefix(_normalize_path(None)).rstrip("/"):
        raise HTTPException(status_code=400, detail="Cannot rename root folder")
    parent = rest.rsplit("/", 1)[0] if "/" in rest[1:] else "/"
    target = f"{parent.rstrip('/')}/{name}"
    target_path = f"{prefix}{target}"
    _ensure_within_root(target_path)
    await move_path(source_path, target_path, overwrite=True)
    return {"path": target_path}


@router.post("/files-catalog/move")
async def move_catalog_item(
    payload: MovePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    from_path = _normalize_path(payload.from_path)
    to_path = _normalize_path(payload.to_path)
    if from_path.startswith("disk:") and not to_path.startswith("disk:"):
        to_path = f"disk:{to_path}"
    if to_path.startswith("disk:") and not from_path.startswith("disk:"):
        from_path = f"disk:{from_path}"
    _ensure_within_root(from_path)
    _ensure_within_root(to_path)
    if _is_root_path(from_path):
        raise HTTPException(status_code=400, detail="Cannot move root folder")
    await move_path(from_path, to_path, overwrite=True)
    return {"path": to_path}


@router.post("/files-catalog/upload")
async def upload_catalog_files(
    request: Request,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    form = await request.form()
    files = form.getlist("files") if form else []
    paths = form.getlist("paths") if form else []
    if not files:
        raise HTTPException(status_code=400, detail="Files are required")
    path = _normalize_path(path)
    _ensure_within_root(path)
    await ensure_path(path)
    if not files:
        raise HTTPException(status_code=400, detail="Files are required")

    def _sanitize_rel_path(value: str) -> str:
        rel = (value or "").replace("\\", "/").strip()
        rel = rel.lstrip("/")
        if not rel:
            return ""
        parts = [p for p in rel.split("/") if p and p not in {".", ".."}]
        clean_parts = [clean_name(p) for p in parts]
        return "/".join([p for p in clean_parts if p])

    skip_names = {"thumbs.db", "desktop.ini", ".ds_store"}
    uploaded = 0
    for idx, upload in enumerate(files):
        raw_rel = None
        if paths and idx < len(paths):
            raw_rel = paths[idx]
        if not raw_rel and upload.filename and ("/" in upload.filename or "\\" in upload.filename):
            raw_rel = upload.filename
        rel_path = _sanitize_rel_path(raw_rel or "")
        file_name = ""
        if rel_path:
            file_name = rel_path.rsplit("/", 1)[-1]
        if not file_name:
            file_name = (upload.filename or "").split("/")[-1].split("\\")[-1]
        if file_name.lower() in skip_names:
            continue
        if rel_path:
            rel_dir = rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""
            if rel_dir:
                await ensure_path(f"{path.rstrip('/')}/{rel_dir}")
            file_path = f"{path.rstrip('/')}/{rel_path}"
        else:
            safe_name = clean_name(upload.filename or "file")
            file_path = f"{path.rstrip('/')}/{safe_name}"
        _ensure_within_root(file_path)
        validate_upload_metadata(upload.filename, upload.content_type)
        max_bytes = settings.UPLOAD_TMP_MAX_BYTES or 0
        if is_local_storage():
            destination = local_path(file_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            size_bytes = 0
            with open(destination, "wb") as out_file:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if max_bytes and size_bytes > max_bytes:
                        out_file.close()
                        destination.unlink(missing_ok=True)
                        raise HTTPException(status_code=413, detail="File is too large")
                    out_file.write(chunk)
            await upload.close()
        else:
            temp_path, _size = await _write_upload_to_tmp(upload, max_bytes)
            try:
                await upload_file_with_safe_extension(file_path, temp_path)
            finally:
                Path(temp_path).unlink(missing_ok=True)
                await upload.close()
        uploaded += 1
    return {"uploaded": uploaded}


@router.delete("/files-catalog")
async def delete_catalog_item(
    request: Request,
    path: str = Query(...),
    permanent: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    path = _normalize_path(path)
    _ensure_within_root(path)
    if _is_root_path(path):
        raise HTTPException(status_code=400, detail="Cannot delete root folder")
    await delete_path(path, permanently=permanent)
    return {"deleted": True, "permanent": permanent}


@router.get("/files-catalog/download")
async def download_catalog_item(
    request: Request,
    path: str = Query(...),
    redirect: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    await _check_access(db, user, request)
    path = _normalize_path(path)
    _ensure_within_root(path)
    href = await get_download_href(path)
    if redirect:
        return RedirectResponse(url=href)
    return {"href": href}
