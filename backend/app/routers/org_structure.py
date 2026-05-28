"""
Organisation structure (org tree) API.

Phase 1: model + admin CRUD + org chart. No impact on existing access — the
`org_structure` section only gates managing the tree itself (non-ownable).
`head_user_id` is stored as metadata here; it becomes functional for the
opt-in subtree permission scope in Phase 2.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import OrgUnit, User
from app.schemas.org_unit import (
    OrgUnitAssign,
    OrgUnitCreate,
    OrgUnitResponse,
    OrgUnitTreeNode,
    OrgUnitUpdate,
)
from app.services.permissions import require_section_read, require_section_write

router = APIRouter()

SECTION = "org_structure"


def _self_path(parent: Optional[OrgUnit], unit_id: str) -> str:
    base = (parent.path if parent and parent.path else "/")
    if not base.endswith("/"):
        base += "/"
    return f"{base}{unit_id}/"


def _depth_of(path: str) -> int:
    # path like '/a/b/c/' -> 3 segments -> depth = segments - 1
    parts = [p for p in (path or "").split("/") if p]
    return max(len(parts) - 1, 0)


async def _member_counts(db: AsyncSession) -> dict:
    res = await db.execute(
        select(User.org_unit_id, func.count(User.id))
        .where(User.org_unit_id.isnot(None))
        .group_by(User.org_unit_id)
    )
    return {str(uid): int(cnt) for uid, cnt in res.all() if uid}


def _to_response(unit: OrgUnit, counts: dict) -> OrgUnitResponse:
    data = OrgUnitResponse.model_validate(unit)
    data.member_count = counts.get(str(unit.id), 0)
    return data


async def _recompute_subtree(db: AsyncSession, root: OrgUnit) -> None:
    """Recompute path/depth for `root` and all its descendants after a move
    or after creation. Admin-only, low frequency — full walk is fine."""
    res = await db.execute(select(OrgUnit))
    all_units = list(res.scalars().all())
    by_parent: dict = {}
    for u in all_units:
        by_parent.setdefault(str(u.parent_id) if u.parent_id else None, []).append(u)

    parent = None
    if root.parent_id:
        parent = next((u for u in all_units if str(u.id) == str(root.parent_id)), None)

    stack = [(root, parent)]
    while stack:
        node, p = stack.pop()
        node.path = _self_path(p, str(node.id))
        node.depth = _depth_of(node.path)
        db.add(node)
        for child in by_parent.get(str(node.id), []):
            stack.append((child, node))


@router.get("/", response_model=List[OrgUnitTreeNode])
async def list_org_units(
    flat: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read(SECTION)),
):
    units = await OrgUnit.get_all(db)
    counts = await _member_counts(db)

    members_by_unit: dict = {}
    res = await db.execute(
        select(User).where(User.org_unit_id.isnot(None))
    )
    for u in res.scalars().all():
        members_by_unit.setdefault(str(u.org_unit_id), []).append(
            {"id": str(u.id), "full_name": u.full_name, "email": u.email}
        )

    nodes = {}
    for unit in units:
        node = OrgUnitTreeNode.model_validate(unit)
        node.member_count = counts.get(str(unit.id), 0)
        node.members = members_by_unit.get(str(unit.id), [])  # type: ignore
        node.children = []
        nodes[str(unit.id)] = node

    if flat:
        return list(nodes.values())

    roots = []
    for unit in units:
        node = nodes[str(unit.id)]
        pid = str(unit.parent_id) if unit.parent_id else None
        if pid and pid in nodes:
            nodes[pid].children.append(node)
        else:
            roots.append(node)
    return roots


@router.get("/{unit_id}", response_model=OrgUnitTreeNode)
async def get_org_unit(
    unit_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_read(SECTION)),
):
    unit = await OrgUnit.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")
    counts = await _member_counts(db)
    node = OrgUnitTreeNode.model_validate(unit)
    node.member_count = counts.get(str(unit.id), 0)

    res = await db.execute(
        select(User).where(User.org_unit_id == str(unit.id))
    )
    node.members = [
        {"id": str(u.id), "full_name": u.full_name, "email": u.email}
        for u in res.scalars().all()
    ]  # type: ignore

    res = await db.execute(
        select(OrgUnit).where(OrgUnit.parent_id == str(unit.id))
        .order_by(OrgUnit.sort_order, OrgUnit.name)
    )
    node.children = [
        OrgUnitTreeNode.model_validate(c) for c in res.scalars().all()
    ]
    return node


@router.post("/", response_model=OrgUnitResponse)
async def create_org_unit(
    payload: OrgUnitCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write(SECTION)),
):
    parent = None
    if payload.parent_id:
        parent = await OrgUnit.get_by_id(db, payload.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Родительский узел не найден")

    unit = OrgUnit(
        name=payload.name,
        parent_id=str(parent.id) if parent else None,
        kind=payload.kind,
        head_user_id=payload.head_user_id,
        sort_order=payload.sort_order or 0,
    )
    db.add(unit)
    await db.flush()  # assign id
    unit.path = _self_path(parent, str(unit.id))
    unit.depth = _depth_of(unit.path)
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return _to_response(unit, await _member_counts(db))


@router.patch("/{unit_id}", response_model=OrgUnitResponse)
async def update_org_unit(
    unit_id: str,
    payload: OrgUnitUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write(SECTION)),
):
    unit = await OrgUnit.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    data = payload.model_dump(exclude_unset=True)
    moved = False

    if "parent_id" in data:
        new_parent_id = data.pop("parent_id")
        new_parent_id = str(new_parent_id) if new_parent_id else None
        if new_parent_id != (str(unit.parent_id) if unit.parent_id else None):
            if new_parent_id == str(unit.id):
                raise HTTPException(status_code=400, detail="Узел не может быть родителем сам себе")
            new_parent = None
            if new_parent_id:
                new_parent = await OrgUnit.get_by_id(db, new_parent_id)
                if not new_parent:
                    raise HTTPException(status_code=400, detail="Родительский узел не найден")
                # cycle guard: new parent must not be inside this subtree
                if new_parent.path and unit.path and new_parent.path.startswith(unit.path):
                    raise HTTPException(
                        status_code=400,
                        detail="Нельзя переместить узел внутрь его собственного поддерева",
                    )
            unit.parent_id = new_parent_id
            moved = True

    for field in ("name", "kind", "head_user_id", "sort_order"):
        if field in data:
            setattr(unit, field, data[field])

    db.add(unit)
    await db.flush()
    if moved:
        await _recompute_subtree(db, unit)
    await db.commit()
    await db.refresh(unit)
    return _to_response(unit, await _member_counts(db))


@router.delete("/{unit_id}")
async def delete_org_unit(
    unit_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write(SECTION)),
):
    unit = await OrgUnit.get_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    child = await db.execute(
        select(func.count(OrgUnit.id)).where(OrgUnit.parent_id == str(unit.id))
    )
    if int(child.scalar() or 0) > 0:
        raise HTTPException(
            status_code=409,
            detail="У узла есть дочерние подразделения — сначала перенесите или удалите их",
        )
    member = await db.execute(
        select(func.count(User.id)).where(User.org_unit_id == str(unit.id))
    )
    if int(member.scalar() or 0) > 0:
        raise HTTPException(
            status_code=409,
            detail="В узле есть сотрудники — сначала переназначьте их",
        )

    await db.execute(delete(OrgUnit).where(OrgUnit.id == str(unit.id)))
    await db.commit()
    return {"message": "Подразделение удалено"}


@router.post("/assign")
async def assign_user(
    payload: OrgUnitAssign,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write(SECTION)),
):
    user = await User.get_by_id(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if payload.org_unit_id:
        unit = await OrgUnit.get_by_id(db, payload.org_unit_id)
        if not unit:
            raise HTTPException(status_code=400, detail="Подразделение не найдено")
        user.org_unit_id = str(unit.id)
    else:
        user.org_unit_id = None
    db.add(user)
    await db.commit()
    return {
        "user_id": str(user.id),
        "org_unit_id": str(user.org_unit_id) if user.org_unit_id else None,
    }
