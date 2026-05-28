"""
Roles and permissions API Router.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import get_db
from app.models import Role, RolePermission, User
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.schemas.role_permission import RolePermissionResponse, RolePermissionSet
from app.services.auth_security_store import revoke_user_tokens
from app.services.permissions import SECTION_KEYS, require_section_read, require_section_write

router = APIRouter()

SECTIONS = SECTION_KEYS


async def _revoke_tokens_for_role_users(db: AsyncSession, role_id: str) -> None:
    result = await db.execute(select(User.id).where(User.role_id == str(role_id)))
    for user_id in result.scalars().all():
        await revoke_user_tokens(str(user_id))


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    return await Role.get_all(db)


@router.post("/", response_model=RoleResponse)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("roles")),
):
    existing = await Role.get_by_name(db, role.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")
    return await Role.create(db, **role.dict())


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    payload: RoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("roles")),
):
    existing = await Role.get_by_id(db, role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    if existing.is_system and not bool(getattr(request.state, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="Системную роль может изменять только системный суперпользователь.")
    role = await Role.update(db, role_id, **payload.dict(exclude_unset=True))
    await _revoke_tokens_for_role_users(db, role_id)
    return role


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("roles")),
):
    role = await Role.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system and not bool(getattr(request.state, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="Системную роль может удалять только системный суперпользователь.")
    if role.is_system:
        raise HTTPException(status_code=400, detail="System role cannot be deleted")
    await _revoke_tokens_for_role_users(db, role_id)
    success = await Role.delete(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted"}


@router.get("/sections", response_model=List[str])
async def list_sections(_=Depends(require_section_read("roles"))):
    return SECTIONS


@router.get("/{role_id}/permissions", response_model=List[RolePermissionResponse])
async def get_role_permissions(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read("roles")),
):
    role = await Role.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return await RolePermission.get_by_role(db, role_id)


@router.put("/{role_id}/permissions", response_model=List[RolePermissionResponse])
async def set_role_permissions(
    role_id: str,
    permissions: List[RolePermissionSet],
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("roles")),
):
    role = await Role.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system and not bool(getattr(request.state, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="Права системной роли может изменять только системный суперпользователь.")
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    await db.commit()

    created = []
    for item in permissions:
        if item.section not in SECTIONS:
            raise HTTPException(status_code=400, detail=f"Unknown section: {item.section}")
        section = item.section
        edit_all = bool(item.edit_all)
        edit_assigned = bool(item.edit_assigned)
        # Implication: edit implies the matching read (cannot edit what you
        # cannot read). Normalized here so the DB is always consistent.
        read_all = bool(item.read_all) or edit_all
        read_assigned = bool(item.read_assigned) or edit_assigned
        permission = RolePermission(
            role_id=role.id,
            section=section,
            read_all=read_all,
            read_assigned=read_assigned,
            edit_all=edit_all,
            edit_assigned=edit_assigned,
        )
        db.add(permission)
        created.append(permission)
    await db.commit()
    result = await db.execute(select(RolePermission).where(RolePermission.role_id == role.id))
    await _revoke_tokens_for_role_users(db, str(role.id))
    return result.scalars().all()
