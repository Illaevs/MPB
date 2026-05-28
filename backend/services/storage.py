"""
Storage helper functions (local filesystem).
"""
import mimetypes
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

from app.core.config import settings


THROTTLED_EXTENSIONS = {"rar", "zip", "7z", "tar", "gz", "mp4", "avi", "mov", "mkv", "db", "sql", "dat"}


def clean_name(name: str, max_len: int = 255) -> str:
    if not name:
        return "Untitled"
    safe = re.sub(r"[^\w\s\-\(\)\.]", "_", name, flags=re.UNICODE).strip()
    safe = re.sub(r"\s+", " ", safe)
    if len(safe) <= max_len:
        return safe
    base, ext = os.path.splitext(safe)
    if ext and len(ext) < max_len:
        trimmed = base[: max_len - len(ext)]
        return f"{trimmed}{ext}"
    return safe[:max_len]


def storage_mode() -> str:
    if settings.STORAGE_BACKEND:
        return settings.STORAGE_BACKEND.strip().lower()
    return "local"


def is_local_storage() -> bool:
    return storage_mode() == "local"


def storage_available() -> bool:
    return bool(settings.STORAGE_LOCAL_ROOT)


def _normalize_path(path: Optional[str]) -> str:
    if not path:
        return "/"
    value = path
    if not value.startswith("/"):
        value = "/" + value
    value = re.sub(r"/+", "/", value)
    return value


def _local_root() -> Path:
    root = settings.STORAGE_LOCAL_ROOT or "/"
    return Path(root).expanduser()


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _local_path(path: str) -> Path:
    root = _local_root().resolve(strict=False)
    normalized = _normalize_path(path)
    candidate = Path(normalized).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve(strict=False)
        if _is_within_root(resolved, root):
            return resolved
        # Backward compatibility: some records store root-relative paths
        # in absolute-like form (e.g. "/legal-work/..." or "//legal-work/...").
        # If path is outside storage root, reinterpret it as root-relative.
        rebased = (root / normalized.lstrip("/")).resolve(strict=False)
        if _is_within_root(rebased, root):
            return rebased
        raise ValueError("Path outside storage root")
    full = (root / normalized.lstrip("/")).resolve(strict=False)
    if not _is_within_root(full, root):
        raise ValueError("Path outside storage root")
    return full


def _legacy_roots() -> List[Path]:
    root = _local_root().resolve(strict=False)
    candidates = [
        root / "Загрузки_из_Приложения",
        root / "Загрузки_из_Почты",
        root / "Р-Р°Р?С?С?Р·РєРё_РёР·_Р?С?РёР>Р?РРчР?РёС?",
    ]
    return [path for path in candidates if path.exists()]


def _resolve_existing_path(path: str) -> Path:
    candidate = _local_path(path)
    if candidate.exists():
        return candidate
    root = _local_root().resolve(strict=False)
    try:
        rel = candidate.relative_to(root)
    except ValueError:
        return candidate
    rel_parts = rel.parts
    candidate_tails = []
    if rel_parts:
        candidate_tails.append(Path(*rel_parts))
        if len(rel_parts) > 1:
            candidate_tails.append(Path(*rel_parts[1:]))

        anchors = {
            "contracts",
            "legal-work",
            "outgoing",
            "accreditations",
            "document-registry",
            "executor",
            "mail",
            "deals",
            "kp",
            "tmp_uploads",
        }
        for idx, part in enumerate(rel_parts):
            if part.lower() in anchors and idx < len(rel_parts) - 1:
                candidate_tails.append(Path(*rel_parts[idx:]))

    seen = set()
    for tail in candidate_tails:
        key = tail.as_posix()
        if key in seen:
            continue
        seen.add(key)

        rebased = (root / tail).resolve(strict=False)
        if _is_within_root(rebased, root) and rebased.exists():
            return rebased

        for alt_root in _legacy_roots():
            alt_root_resolved = alt_root.resolve(strict=False)
            alt_path = (alt_root_resolved / tail).resolve(strict=False)
            if _is_within_root(alt_path, alt_root_resolved) and alt_path.exists():
                return alt_path
    return candidate


def local_path(path: str) -> Path:
    return _local_path(path)


async def ensure_path(path: str) -> None:
    local_dir = _local_path(path)
    local_dir.mkdir(parents=True, exist_ok=True)


async def list_items(path: str, limit: int = 100) -> List[Dict]:
    local_dir = _local_path(path)
    if not local_dir.exists() or not local_dir.is_dir():
        return []
    base_path = _normalize_path(path).rstrip("/")
    items: List[Dict] = []
    for entry in sorted(local_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        entry_path = f"{base_path}/{entry.name}" if base_path else f"/{entry.name}"
        stat = entry.stat()
        modified = datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
        created = datetime.utcfromtimestamp(stat.st_ctime).isoformat() + "Z"
        mime_type, _ = mimetypes.guess_type(entry.name)
        ext_hint = None
        if entry.is_file() and "." not in entry.name:
            try:
                with open(entry, "rb") as fh:
                    header = fh.read(4)
                if header.startswith(b"%PDF"):
                    ext_hint = "PDF"
            except Exception:
                ext_hint = None
        items.append(
            {
                "name": entry.name,
                "type": "folder" if entry.is_dir() else "file",
                "path": entry_path,
                "url": None,
                "size": stat.st_size if entry.is_file() else None,
                "modified": modified,
                "created": created,
                "mime_type": mime_type,
                "ext_hint": ext_hint,
            }
        )
        if len(items) >= limit:
            break
    return items


async def search_items(text: str, path: Optional[str] = None, limit: int = 100) -> List[Dict]:
    base_path = _normalize_path(path) if path else "/"
    local_dir = _local_path(base_path)
    if not local_dir.exists() or not local_dir.is_dir():
        return []
    needle = (text or "").lower()
    matches: List[Dict] = []
    for root, dirs, files in os.walk(local_dir):
        for name in dirs + files:
            if needle not in name.lower():
                continue
            full = Path(root) / name
            rel = full.relative_to(local_dir)
            rel_path = f"{_normalize_path(base_path).rstrip('/')}/{rel.as_posix()}"
            entry_path = rel_path
            stat = full.stat()
            modified = datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
            created = datetime.utcfromtimestamp(stat.st_ctime).isoformat() + "Z"
            mime_type, _ = mimetypes.guess_type(name)
            matches.append(
                {
                    "name": name,
                    "type": "folder" if full.is_dir() else "file",
                    "path": entry_path,
                    "url": None,
                    "size": stat.st_size if full.is_file() else None,
                    "modified": modified,
                    "created": created,
                    "mime_type": mime_type,
                }
            )
            if len(matches) >= limit:
                return matches
    return matches


async def publish(path: str) -> Optional[str]:
    return await get_download_href(path)


async def get_download_href(path: str) -> str:
    encoded = quote(path, safe="")
    return f"/api/v1/storage/download?path={encoded}"


async def delete_path(path: str, permanently: bool = True) -> None:
    local_path = _local_path(path)
    if local_path.is_dir():
        shutil.rmtree(local_path, ignore_errors=True)
    else:
        local_path.unlink(missing_ok=True)


async def move_path(from_path: str, to_path: str, overwrite: bool = True) -> None:
    source = _local_path(from_path)
    target = _local_path(to_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError("Target already exists")
    if target.exists() and overwrite:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink(missing_ok=True)
    shutil.move(str(source), str(target))


def _is_risky_extension(path: str) -> bool:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return ext in THROTTLED_EXTENSIONS


async def upload_bytes_with_safe_extension(path: str, content: bytes) -> None:
    local_path = _local_path(path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)


async def upload_file_with_safe_extension(path: str, local_path: str) -> None:
    destination = _local_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(local_path, destination)


def upload_file_with_safe_extension_sync(path: str, local_path: str) -> None:
    destination = _local_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(local_path, destination)


async def read_file_bytes(path: str) -> bytes:
    local_path = _resolve_existing_path(path)
    if not local_path.exists():
        raise FileNotFoundError(path)
    return local_path.read_bytes()
