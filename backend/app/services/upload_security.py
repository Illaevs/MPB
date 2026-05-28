"""
Upload validation and temporary file hygiene helpers.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.services.storage import clean_name

BLOCKED_UPLOAD_EXTENSIONS = {
    ".apk", ".appimage", ".bat", ".cmd", ".com", ".cpl", ".dll", ".exe", ".hta",
    ".html", ".htm", ".jar", ".js", ".lnk", ".mjs", ".msi", ".php", ".phar",
    ".phtml", ".pl", ".ps1", ".py", ".rb", ".scr", ".sh", ".svg", ".svgz",
    ".vbe", ".vbs", ".wsf", ".xhtml",
}

ALLOWED_UPLOAD_EXTENSIONS = {
    ".7z", ".bmp", ".csv", ".doc", ".docx", ".dwg", ".dxf", ".eml", ".gif",
    ".jpeg", ".jpg", ".msg", ".ods", ".odt", ".pdf", ".png", ".ppt", ".pptx",
    ".rar", ".rtf", ".sig", ".txt", ".tif", ".tiff", ".webp", ".xls", ".xlsx",
    ".xml", ".zip",
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

HTML_SIGNATURES = (
    b"<!doctype html",
    b"<html",
    b"<head",
    b"<body",
    b"<script",
    b"<svg",
    b"<?php",
    b"<%",
)

EXECUTABLE_SIGNATURES = (
    b"MZ",
    b"\x7fELF",
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
)


def tmp_upload_dir() -> Path:
    if settings.UPLOAD_TMP_DIR:
        return Path(settings.UPLOAD_TMP_DIR)
    base = Path(__file__).resolve().parents[3]
    return base / "tmp_uploads"


def validate_upload_metadata(filename: str | None, content_type: str | None) -> str:
    safe_name = clean_name(filename or "upload")
    suffix = Path(safe_name).suffix.lower()
    media_type = (content_type or "").lower()
    if suffix in BLOCKED_UPLOAD_EXTENSIONS or media_type in BLOCKED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Этот тип файла запрещен к загрузке.")
    if suffix and suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла.")
    return safe_name


def validate_upload_signature(chunk: bytes) -> None:
    if not chunk:
        return
    head = chunk[:8192]
    lowered = head.lstrip().lower()

    if any(head.startswith(signature) for signature in EXECUTABLE_SIGNATURES):
        raise HTTPException(status_code=400, detail="Исполняемые файлы запрещены к загрузке.")

    if lowered.startswith(b"#!"):
        raise HTTPException(status_code=400, detail="Скрипты запрещены к загрузке.")

    if any(lowered.startswith(signature) for signature in HTML_SIGNATURES):
        raise HTTPException(status_code=400, detail="HTML, SVG и похожие файлы запрещены к загрузке.")


def _iter_tmp_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return (path for path in root.rglob("*") if path.is_file())


def cleanup_temp_uploads() -> dict[str, int]:
    root = tmp_upload_dir()
    root.mkdir(parents=True, exist_ok=True)
    ttl_seconds = max(int(settings.UPLOAD_TMP_TTL_HOURS or 0), 1) * 3600
    now = time.time()
    removed_files = 0
    freed_bytes = 0
    for path in list(_iter_tmp_files(root)):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        if now - stat.st_mtime < ttl_seconds:
            continue
        try:
            freed_bytes += stat.st_size
            path.unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            continue
    return {"removed_files": removed_files, "freed_bytes": freed_bytes}


def tmp_uploads_total_bytes() -> int:
    root = tmp_upload_dir()
    root.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in _iter_tmp_files(root):
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return total


def ensure_tmp_capacity(required_bytes: int = 0) -> None:
    cleanup_temp_uploads()
    limit = int(settings.UPLOAD_TMP_TOTAL_MAX_BYTES or 0)
    if not limit:
        return
    current = tmp_uploads_total_bytes()
    if current + max(required_bytes, 0) > limit:
        raise HTTPException(
            status_code=507,
            detail="Временное хранилище загрузок переполнено. Повторите попытку позже.",
        )


async def write_upload_to_tmp(upload: UploadFile, max_bytes: int) -> tuple[str, int]:
    safe_name = validate_upload_metadata(upload.filename, upload.content_type)
    ensure_tmp_capacity(max_bytes)
    root = tmp_upload_dir()
    root.mkdir(parents=True, exist_ok=True)
    temp_name = f"{uuid.uuid4()}_{safe_name}"
    temp_path = root / temp_name

    size_bytes = 0
    signature_checked = False
    with open(temp_path, "wb") as out_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            if not signature_checked:
                validate_upload_signature(chunk)
                signature_checked = True
            size_bytes += len(chunk)
            if size_bytes > max_bytes:
                out_file.close()
                temp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Файл слишком большой.")
            out_file.write(chunk)

    return str(temp_path), size_bytes
