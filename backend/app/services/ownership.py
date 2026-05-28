"""
Single source of truth for "is this record mine?" (ownership) across the
permission system.

Read scoping for "assigned" already works per-router today (allowed_deal_ids,
responsible_user_id filters, etc.); this module adds the *record-level*
ownership predicate used by edit enforcement (`edit_assigned` => may edit only
owned records).

Phase 2 (opt-in, head-based): when the user's role has `subtree_scope` and the
user is the head of one or more org_units, "mine" expands from `{me}` to
`{me} ∪ {everyone in those units' subtrees}` (recursive via OrgUnit.path).
Flag OFF or non-head ⇒ scope stays `{me}` ⇒ behaviour identical to before.

Decision (per approved plan):
- Ownership reuses existing fields; no new owner columns.
- Contract / IncomeExpense ownership is transitive via the linked deal
  (deal where the user is a GIP — DealGip).
"""
from typing import Iterable, List, Optional, Set

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DealGip, OrgUnit, Role, User

# Sections that have a meaningful per-record owner. For everything else
# `*_assigned` collapses to `*_all` (no per-record narrowing).
OWNABLE_SECTIONS = frozenset({
    "projects",
    "contracts",
    "income_expense",
    "outgoing_registry",
    "leads",
    "tasks",
    # Свои отсутствия пользователь создаёт/правит сам — edit_assigned.
    # «Своё» = `user_absences.user_id == me`.
    "absences",
})


def is_section_ownable(section: Optional[str]) -> bool:
    return str(section or "") in OWNABLE_SECTIONS


async def _role_subtree_enabled(db: AsyncSession, user) -> bool:
    role_id = getattr(user, "role_id", None)
    if not role_id:
        return False
    res = await db.execute(
        select(Role.subtree_scope).where(Role.id == str(role_id))
    )
    return bool(res.scalar_one_or_none())


async def subtree_user_ids(db: AsyncSession, user) -> Set[str]:
    """Head-based scope expansion. Returns `{me}` unless the user's role has
    `subtree_scope` AND the user is the head of at least one org_unit — then
    also includes every user attached to that unit or any descendant unit
    (recursive via the materialised `path`)."""
    uid = str(getattr(user, "id", "") or "")
    base: Set[str] = {uid} if uid else set()
    if not uid:
        return base
    if not await _role_subtree_enabled(db, user):
        return base

    res = await db.execute(
        select(OrgUnit.path).where(OrgUnit.head_user_id == uid)
    )
    paths = [p for (p,) in res.all() if p]
    if not paths:
        return base

    conds = [OrgUnit.path.like(p + "%") for p in paths]
    res = await db.execute(select(OrgUnit.id).where(or_(*conds)))
    unit_ids = [str(i) for (i,) in res.all()]
    if not unit_ids:
        return base

    res = await db.execute(
        select(User.id).where(User.org_unit_id.in_(unit_ids))
    )
    ids = {str(i) for (i,) in res.all()}
    ids |= base
    return ids


async def owned_deal_ids(
    db: AsyncSession,
    user,
    scope_user_ids: Optional[Iterable[str]] = None,
) -> List[str]:
    """Deal ids where the user (or, when `scope_user_ids` is given, any user
    in that set) is assigned as GIP — the canonical "my deals". When
    `scope_user_ids` is None it falls back to strictly the user's own deals
    (behaviour identical to before Phase 2)."""
    if scope_user_ids is None:
        if not user or not getattr(user, "id", None):
            return []
        scope_user_ids = {str(user.id)}
    scope = [str(s) for s in scope_user_ids if s]
    if not scope:
        return []
    result = await db.execute(
        select(DealGip.deal_id).where(DealGip.user_id.in_(scope))
    )
    return [str(item[0]) for item in result.all()]


def _val(record, attr) -> str:
    return str(getattr(record, attr, "") or "")


async def is_owned(db: AsyncSession, section: str, record, user) -> bool:
    """True if `record` belongs to `user` for the given section (with the
    head-based subtree expansion when enabled).

    Non-ownable sections return True (no per-record restriction — the
    section-level edit grant already decided access)."""
    section = str(section or "")
    if section not in OWNABLE_SECTIONS:
        return True
    if record is None or not user or not getattr(user, "id", None):
        return False

    scope = await subtree_user_ids(db, user)

    if section == "leads":
        return _val(record, "responsible_user_id") in scope

    if section == "tasks":
        return (
            _val(record, "assigned_to_user_id") in scope
            or _val(record, "created_by_user_id") in scope
        )

    if section == "outgoing_registry":
        return _val(record, "created_by") in scope

    if section == "projects":
        rec_id = getattr(record, "id", None)
        if rec_id is None:
            return False
        return str(rec_id) in set(await owned_deal_ids(db, user, scope))

    if section in ("contracts", "income_expense"):
        deal_id = getattr(record, "deal_id", None)
        if deal_id is None:
            return False
        return str(deal_id) in set(await owned_deal_ids(db, user, scope))

    return False
