"""
Permission helpers for role-based filtering.

Matrix is 4 flags per section: read_all / read_assigned / edit_all /
edit_assigned. Implication is enforced everywhere it's read:
edit_all => read_all, edit_assigned => read_assigned (you cannot edit
what you cannot read). Write enforcement uses the edit_* flags; record
level "own" narrowing is delegated to app.services.ownership.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import DealGip, RolePermission, User
from app.services.ownership import (
    is_owned,
    is_section_ownable,
    owned_deal_ids as _owned_deal_ids,
    subtree_user_ids,
)

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
    "org_structure",
    "support",
    "data_health",
    "workday_admin",
    # Карточка сотрудника = доступна любому авторизованному (вью).
    # Секция `absences` гейтит создание/правку: edit_assigned — свои
    # отсутствия, edit_all — чужие (только админ).
    "absences",
    # Лента новостей: читают/комментируют/лайкают все авторизованные;
    # публиковать/править/удалять посты — только `feed.edit_all`.
    "feed",
]

SECTION_KEYS = [*AUTHENTICATED_SECTION_KEYS, "customer_portal"]

_SAFE_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass(frozen=True)
class SectionAcl:
    """Effective per-section access (implication already applied)."""
    read_all: bool = False
    read_assigned: bool = False
    edit_all: bool = False
    edit_assigned: bool = False

    @property
    def can_read(self) -> bool:
        return self.read_all or self.read_assigned

    @property
    def can_write(self) -> bool:
        """Section-level write gate (collection / create)."""
        return self.edit_all or self.edit_assigned


def _acl_from_perm(perm: Optional[RolePermission]) -> SectionAcl:
    if not perm:
        return SectionAcl()
    edit_all = bool(getattr(perm, "edit_all", False))
    edit_assigned = bool(getattr(perm, "edit_assigned", False))
    # Implication: edit implies the matching read (defensive — also
    # normalized on save, but DB rows may predate that).
    return SectionAcl(
        read_all=bool(perm.read_all) or edit_all,
        read_assigned=bool(perm.read_assigned) or edit_assigned,
        edit_all=edit_all,
        edit_assigned=edit_assigned,
    )


async def get_section_acl(
    db: AsyncSession,
    role_id: Optional[str],
    section: str,
) -> SectionAcl:
    if not role_id:
        return SectionAcl()
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(role_id),
            RolePermission.section == section,
        )
    )
    return _acl_from_perm(result.scalar_one_or_none())


async def get_sections_acl(
    db: AsyncSession,
    role_id: Optional[str],
    sections: Iterable[str],
) -> Dict[str, SectionAcl]:
    normalized = [section for section in dict.fromkeys(str(section) for section in sections if section)]
    if not role_id or not normalized:
        return {}
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(role_id),
            RolePermission.section.in_(normalized),
        )
    )
    return {str(perm.section): _acl_from_perm(perm) for perm in result.scalars().all()}


async def get_section_permissions(
    db: AsyncSession,
    role_id: Optional[str],
    section: str,
) -> Tuple[bool, bool]:
    """Back-compat: returns effective (read_all, read_assigned)."""
    acl = await get_section_acl(db, role_id, section)
    return acl.read_all, acl.read_assigned


async def get_sections_permissions(
    db: AsyncSession,
    role_id: Optional[str],
    sections: Iterable[str],
) -> Dict[str, Tuple[bool, bool]]:
    acl_map = await get_sections_acl(db, role_id, sections)
    return {sec: (acl.read_all, acl.read_assigned) for sec, acl in acl_map.items()}


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
    """Section-level write gate. Passes if the role has edit_all OR
    edit_assigned for the section. Record-level "own only" narrowing for
    ownable sections must be enforced in the handler via
    ensure_can_edit_record() after the target row is loaded."""
    async def _dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(CurrentUser),
    ) -> User:
        if is_superuser(request):
            return user
        acl = await get_section_acl(db, user.role_id, section)
        if not acl.can_write:
            raise HTTPException(status_code=403, detail=f"Нет прав на изменение раздела: {section}")
        return user

    return _dependency


async def can_edit_record(
    db: AsyncSession,
    request: Request,
    user: User,
    section: str,
    record,
) -> bool:
    """Record-level edit check: edit_all => any; edit_assigned => only if
    the record is owned by the user (non-ownable sections: edit_assigned
    behaves like edit_all)."""
    if is_superuser(request):
        return True
    acl = await get_section_acl(db, user.role_id, section)
    if acl.edit_all:
        return True
    if not acl.edit_assigned:
        return False
    if not is_section_ownable(section):
        return True
    return await is_owned(db, section, record, user)


async def ensure_can_edit_record(
    db: AsyncSession,
    request: Request,
    user: User,
    section: str,
    record,
) -> None:
    if not await can_edit_record(db, request, user, section, record):
        raise HTTPException(
            status_code=403,
            detail=f"Нет прав на изменение этой записи раздела: {section}",
        )


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

        # Self-service endpoints (/users/me/*) are CurrentUser-scoped
        # (own profile, UI preferences, wallpaper, avatar). They must not
        # require admin section access — a read-only user must be able to
        # read AND update their own settings.
        if "/users/me/" in request.url.path:
            return user

        acl_map = await get_sections_acl(db, user.role_id, normalized_sections)
        wants_write = request.method.upper() not in _SAFE_HTTP_METHODS

        for section in normalized_sections:
            acl = acl_map.get(section, SectionAcl())
            if wants_write:
                if acl.can_write:
                    return user
            else:
                if acl.can_read:
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
    # Head-based subtree expansion when the role opted in; otherwise this
    # resolves to exactly the user's own GIP deals (no behaviour change).
    scope = await subtree_user_ids(db, user)
    return await _owned_deal_ids(db, user, scope)
