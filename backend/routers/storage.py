"""
Local storage download helper.
"""
import mimetypes
import os
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.services.storage import _local_path, is_local_storage, read_file_bytes, storage_available


router = APIRouter()
_USAGE_CACHE = {"ts": 0.0, "data": None}


def _is_admin(request: Request) -> bool:
    return bool(getattr(request.state, "is_superuser", False))


def _require_admin(request: Request) -> None:
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin access required")


def _storage_root_path() -> Path:
    root = settings.STORAGE_LOCAL_ROOT or "/"
    if root.startswith("disk:"):
        root = root[5:]
    return Path(root)


def _get_usage_cached(path: Path, ttl: int = 600) -> dict:
    now = time.time()
    cached = _USAGE_CACHE.get("data")
    ts = _USAGE_CACHE.get("ts", 0.0)
    if cached and (now - ts) < ttl:
        return cached
    usage = shutil.disk_usage(str(path))
    total = int(usage.total)
    free = int(usage.free)
    used = max(total - free, 0)
    percent = round((used / total) * 100, 1) if total else 0
    data = {"used_bytes": used, "free_bytes": free, "total_bytes": total, "percent": percent}
    _USAGE_CACHE["data"] = data
    _USAGE_CACHE["ts"] = now
    return data


@router.get("/storage/download")
async def download_storage_item(
    request: Request,
    path: str = Query(...),
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    decoded = unquote(path)
    filename = Path(decoded.replace("disk:", "")).name or "file"
    mime_type, _ = mimetypes.guess_type(filename)
    if is_local_storage():
        try:
            local_path = _local_path(decoded)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid path")
        if local_path.exists() and local_path.is_dir():
            zip_name = f"{filename}.zip" if not filename.lower().endswith(".zip") else filename
            tmp_dir = tempfile.mkdtemp(prefix="crm_zip_")
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
        content = await read_file_bytes(decoded)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to download file")
    encoded_name = quote(filename, safe="")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    return Response(content=content, media_type=mime_type or "application/octet-stream", headers=headers)


@router.get("/storage/usage")
async def storage_usage(
    request: Request,
    user=Depends(CurrentUser),
):
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    _require_admin(request)
    if not is_local_storage():
        raise HTTPException(status_code=400, detail="Storage usage is only available for local storage")
    root_path = _storage_root_path()
    if not root_path.exists():
        raise HTTPException(status_code=500, detail="Storage root not found")
    return _get_usage_cached(root_path)
