"""
Helper service for the "наша компания" default.

Single source of truth for filling `our_company_id` when the frontend
no longer asks the user to pick it (planned: one internal company,
no UI selector). Routers call `apply_default_our_company` before
persisting create/update payloads.
"""
from typing import Any, Mapping, MutableMapping, Optional

from app.models import Company


async def get_default_id(db) -> Optional[str]:
    """Returns the id of the internal company flagged is_default=True,
    or None if no default is configured."""
    return await Company.get_default_our_company_id(db)


def _is_empty(value: Any) -> bool:
    """True for None, empty string, and the literal "null" string that
    some legacy frontends send instead of dropping the field."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "null", "none"}:
        return True
    return False


async def apply_default_our_company(
    db,
    payload: MutableMapping[str, Any],
    *,
    field: str = "our_company_id",
) -> Optional[str]:
    """If `payload[field]` is missing/empty, fill it with the default.
    Mutates the dict in place; returns the resolved id (or None if no
    default is configured)."""
    current = payload.get(field) if isinstance(payload, Mapping) else None
    if not _is_empty(current):
        return current
    default_id = await get_default_id(db)
    if default_id:
        payload[field] = default_id
    return default_id
