"""Fail-closed per-record authorization for raw-path file access.

Historically `GET /api/v1/storage/download?path=` (and the executor /
files_catalog raw-path endpoints) only checked "authenticated + holds ANY one
of ~30 section permissions", letting any user read the entire storage tree by
guessing/altering paths. This module re-derives the owning record/section from
the requested path and enforces the same read scoping the rest of the app uses:

* superuser            -> allow
* deal-scoped roots     -> `[#<deal_id>] ...` must be in the user's allowed deals
* /contracts/<id>/...   -> contracts read_all OR (read_assigned AND owned deal)
* known section prefix  -> requires read on that section
* anything else         -> denied (fail-closed)

It tightens, but never widens, access — superuser and read_all behaviour is
unchanged, so legitimate flows keep working.
"""
import re
from typing import Iterable, Tuple

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Contract, User
from app.services.ownership import is_owned
from app.services.permissions import (
    allowed_deal_ids,
    get_section_acl,
    is_superuser,
)

_DEAL_TAG_RE = re.compile(r"\[#([0-9a-fA-F-]{6,})\]")
_CONTRACT_RE = re.compile(r"(?:^|/)contracts/([0-9a-fA-F-]{8,})(?:/|$)")

# Top-level path segment -> section keys that grant read of that subtree.
_PREFIX_SECTIONS = {
    "accreditations": ("accreditations_admin", "accreditations_subcontractor"),
    "companies": ("companies",),
    "document-templates": ("document_templates",),
    "legal-work": ("legal_work",),
    "legal_work": ("legal_work",),
    "outgoing": ("outgoing_registry",),
    "outgoing-registry": ("outgoing_registry",),
    "document-registry": ("document_registry",),
    "kp": ("projects", "leads"),
    "mail": ("mail",),
}

_DENIED = HTTPException(status_code=403, detail="Нет доступа к этому файлу")


async def _section_readable(
    db: AsyncSession, request: Request, user: User, sections: Iterable[str]
) -> bool:
    for section in sections:
        acl = await get_section_acl(db, user.role_id, section)
        if acl.can_read:
            return True
    return False


async def authorize_storage_path(
    db: AsyncSession, request: Request, user: User, path: str
) -> None:
    """Raise 403 unless `user` is allowed to read the record that owns `path`."""
    if is_superuser(request):
        return

    decoded = (path or "").replace("disk:", "").replace("\\", "/")

    # 1. Deal-scoped storage roots: "[#<deal_id>] <title> (ТЗ|Прочее|Результаты)"
    tag = _DEAL_TAG_RE.search(decoded)
    if tag:
        deal_id = tag.group(1).strip()
        allowed = await allowed_deal_ids(db, request, user)
        if allowed is None or deal_id in set(str(d) for d in allowed):
            return
        raise _DENIED

    # 2. /contracts/<contract_id>/... -> contracts section + deal ownership
    cm = _CONTRACT_RE.search(decoded)
    if cm:
        acl = await get_section_acl(db, user.role_id, "contracts")
        if not acl.can_read:
            raise _DENIED
        if acl.read_all:
            return
        contract = await db.get(Contract, cm.group(1))
        if not contract:
            raise HTTPException(status_code=404, detail="File not found")
        if await is_owned(db, "contracts", contract, user):
            return
        raise _DENIED

    # 3. Known section-scoped prefixes (segment anywhere in the path).
    for seg in (s for s in decoded.split("/") if s):
        sections = _PREFIX_SECTIONS.get(seg.lower())
        if sections:
            if await _section_readable(db, request, user, sections):
                return
            raise _DENIED

    # 4. Unrecognised path shape -> fail closed.
    raise _DENIED
