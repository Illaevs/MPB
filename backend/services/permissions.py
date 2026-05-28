"""
Permission helpers for role-based filtering.
"""
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import DealGip, RolePermission, User

AUTHENTICATED_SECTION_KEYS = [
    "projects",
    "leads",
    "companies",
    "contracts",
    "catalog",
    "tasks",
    "task_chat",
    "global_chat",
    "calendar",
    "legal_work",
    "task_auctions_manage",
    "task_auctions_bid",
    "tasks_penalties_manage",
    "finance",
    "treasury",
    "income_expense",
    "executor",
    "outgoing_registry",
    "document_registry",
    "files_catalog",
    "mail",
    "work_results_reviews",
    "tenders_admin",
    "tenders_subcontractor",
    "accreditations_admin",
    "accreditations_subcontractor",
    "users",
    "roles",
    "document_templates",
]

SECTION_KEYS = [*AUTHENTICATED_SECTION_KEYS, "customer_portal"]

_SAFE_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}


async def get_section_permissions(
    db: AsyncSession,
    role_id: Optional[str],
    section: str,
) -> Tuple[bool, bool]:
    if not role_id:
        return False, False
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(role_id),
            RolePermission.section == section,
        )
    )
    perm = result.scalar_one_or_none()
    return bool(perm and perm.read_all), bool(perm and perm.read_assigned)


async def get_sections_permissions(
    db: AsyncSession,
    role_id: Optional[str],
    sections: Iterable[str],
) -> Dict[str, Tuple[bool, bool]]:
    normalized = [section for section in dict.fromkeys(str(section) for section in sections if section)]
    if not role_id or not normalized:
        return {}
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(role_id),
            RolePermission.section.in_(normalized),
        )
    )
    permissions: Dict[str, Tuple[bool, bool]] = {}
    for perm in result.scalars().all():
        permissions[str(perm.section)] = (bool(perm.read_all), bool(perm.read_assigned))
    return permissions


def is_superuser(request: Request) -> bool:
    return bool(getattr(request.state, "is_superuser", False))


def require_section_read(section: str):
    async def _dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(CurrentUser),
    ) -> User:
        if is_superuser(request):
            return user
        read_all, read_assigned = await get_section_permissions(db, user.role_id, section)
        if not (read_all or read_assigned):
            raise HTTPException(status_code=403, detail=f"Нет доступа к разделу: {section}")
        return user

    return _dependency


def require_section_write(section: str):
    async def _dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(CurrentUser),
    ) -> User:
        if is_superuser(request):
            return user
        read_all, _ = await get_section_permissions(db, user.role_id, section)
        if not read_all:
            raise HTTPException(status_code=403, detail=f"Нет прав на изменение раздела: {section}")
        return user

    return _dependency


def require_any_section_access(*sections: str):
    normalized_sections = [section for section in dict.fromkeys(str(section) for section in sections if section)]
    if not normalized_sections:
        raise ValueError("At least one section is required")

    async def _dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(CurrentUser),
    ) -> User:
        if is_superuser(request):
            return user

        permissions = await get_sections_permissions(db, user.role_id, normalized_sections)
        wants_write = request.method.upper() not in _SAFE_HTTP_METHODS

        for section in normalized_sections:
            read_all, read_assigned = permissions.get(section, (False, False))
            if wants_write:
                if read_all:
                    return user
            else:
                if read_all or read_assigned:
                    return user

        if wants_write:
            sections_label = ", ".join(normalized_sections)
            raise HTTPException(status_code=403, detail=f"Нет прав на изменение разделов: {sections_label}")
        sections_label = ", ".join(normalized_sections)
        raise HTTPException(status_code=403, detail=f"Нет доступа к разделам: {sections_label}")

    return _dependency


def require_section_access(section: str):
    return require_any_section_access(section)


async def allowed_deal_ids(
    db: AsyncSession,
    request: Request,
    user: User,
) -> Optional[List[str]]:
    if is_superuser(request):
        return None
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "projects")
    if read_all:
        return None
    if not read_assigned:
        return []
    result = await db.execute(select(DealGip.deal_id).where(DealGip.user_id == str(user.id)))
    return [str(item[0]) for item in result.all()]
