"""
Users API Router.
"""
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.security import hash_password
from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models import User, Role, Company, CompanyUserLink
from app.schemas.user import CompanyLinkCreate, UserCreate, UserUpdate, UserResponse
from app.services.auth_security_store import revoke_user_tokens
from app.services.permissions import get_section_permissions, require_section_write
from app.services.user_avatar_bootstrap import avatars_root, ensure_user_avatar_schema

router = APIRouter()

MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _parse_uuid(value: Optional[str], field_name: str) -> Optional[uuid.UUID]:
    if value is None:
        return None
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def _uuid_variants(value: Optional[str]) -> List[str]:
    if not value:
        return []
    raw = str(value)
    variants = {raw}
    try:
        u = uuid.UUID(raw)
        variants.add(u.hex)
        variants.add(str(u))
    except (ValueError, TypeError):
        if len(raw) == 32:
            try:
                u = uuid.UUID(hex=raw)
                variants.add(str(u))
            except (ValueError, TypeError):
                pass
    return list(variants)


def _avatar_path_from_url(url: Optional[str]) -> Optional[Path]:
    if not url:
        return None
    clean_url = str(url).split("?", 1)[0]
    prefixes = ("/static/avatars/", "/api/v1/users/avatar/", "/api/v1/users/avatar-file/")
    if not any(clean_url.startswith(prefix) for prefix in prefixes):
        return None
    filename = Path(clean_url).name
    target = avatars_root() / filename
    try:
        target.resolve().relative_to(avatars_root().resolve())
    except Exception:
        return None
    return target


def _latest_avatar_fallback(filename: str) -> Optional[Path]:
    safe_name = Path(filename).name
    if safe_name != filename or "-" not in safe_name:
        return None
    stem = Path(safe_name).stem
    user_prefix = ""
    if "-" in stem:
        maybe_user, maybe_random = stem.rsplit("-", 1)
        if maybe_user and len(maybe_random) == 32 and all(ch in "0123456789abcdefABCDEF" for ch in maybe_random):
            user_prefix = maybe_user
    if not user_prefix:
        user_prefix = safe_name.split("-", 1)[0]
    if not user_prefix:
        return None
    candidates = []
    for variant in _uuid_variants(user_prefix) or [user_prefix]:
        candidates.extend([path for path in avatars_root().glob(f"{variant}-*") if path.is_file()])
    candidates = list({str(path): path for path in candidates}.values())
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def _resolve_avatar_for_user(user_id: str, avatar_url: Optional[str]) -> Optional[Path]:
    direct = _avatar_path_from_url(avatar_url)
    if direct and direct.exists() and direct.is_file():
        return direct
    candidates = []
    for variant in _uuid_variants(user_id) or [user_id]:
        candidates.extend([path for path in avatars_root().glob(f"{variant}-*") if path.is_file()])
    candidates = list({str(path): path for path in candidates}.values())
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    query = select(User)
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "users")
    if not read_all:
        if not read_assigned:
            return []
        query = query.where(User.id == str(user.id))
    if role_id:
        query = query.where(User.role_id == role_id)
    result = await db.execute(query.order_by(User.full_name.asc()))
    return result.scalars().all()


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    ensure_user_avatar_schema()

    content_type = (file.content_type or "").lower()
    ext = ALLOWED_AVATAR_TYPES.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="Допустимы только JPG, PNG, WEBP или GIF")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="Максимальный размер аватара 5 МБ")

    current_user = await User.get_by_id(db, str(user.id))
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_avatar_path = _resolve_avatar_for_user(str(current_user.id), current_user.avatar_url)
    filename = f"{current_user.id}-{uuid.uuid4().hex}{ext}"
    target = avatars_root() / filename
    target.write_bytes(content)

    try:
        current_user.avatar_url = f"/api/v1/users/avatar-user/{current_user.id}"
        await db.commit()
        await db.refresh(current_user)
    except Exception:
        if target.exists():
            target.unlink()
        raise

    if old_avatar_path and old_avatar_path.exists() and old_avatar_path != target:
        old_avatar_path.unlink(missing_ok=True)

    return current_user


@router.get("/avatar-file/{filename}")
async def get_avatar_file_v2(
    filename: str,
    _user=Depends(CurrentUser),
):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="???????????????????????? ?????? ??????????")
    target = avatars_root() / safe_name
    try:
        target.resolve().relative_to(avatars_root().resolve())
    except Exception:
        raise HTTPException(status_code=400, detail="???????????????????????? ????????")
    if not target.exists() or not target.is_file():
        fallback = _latest_avatar_fallback(safe_name)
        if fallback is None:
            raise HTTPException(status_code=404, detail="???????????? ???? ????????????")
        target = fallback
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(str(target), media_type=media_type, filename=target.name)


@router.get("/avatar-user/{user_id}")
async def get_avatar_by_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(CurrentUser),
):
    current_user = await User.get_by_id(db, user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="Аватар не найден")
    target = _resolve_avatar_for_user(str(current_user.id), current_user.avatar_url)
    if target is None:
        raise HTTPException(status_code=404, detail="Аватар не найден")
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(str(target), media_type=media_type, filename=target.name)


@router.get("/avatar/{filename}")
async def get_avatar_file(
    filename: str,
    _user=Depends(CurrentUser),
):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="???????????????????????? ?????? ??????????")
    target = avatars_root() / safe_name
    try:
        target.resolve().relative_to(avatars_root().resolve())
    except Exception:
        raise HTTPException(status_code=400, detail="???????????????????????? ????????")
    if not target.exists() or not target.is_file():
        fallback = _latest_avatar_fallback(safe_name)
        if fallback is None:
            raise HTTPException(status_code=404, detail="???????????? ???? ????????????")
        target = fallback
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(str(target), media_type=media_type, filename=target.name)


@router.get("/company-links")
async def list_company_links(
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "users")
    if not read_all:
        if not read_assigned:
            return []
        result = await db.execute(select(CompanyUserLink).where(CompanyUserLink.user_id == str(user.id)))
    else:
        result = await db.execute(select(CompanyUserLink))
    links = result.scalars().all()
    if not links:
        return []

    company_ids: List[str] = []
    for link in links:
        company_ids.extend(_uuid_variants(link.company_id))

    company_map = {}
    if company_ids:
        comp_result = await db.execute(select(Company).where(Company.id.in_(list(set(company_ids)))))
        for comp in comp_result.scalars().all():
            for key in _uuid_variants(comp.id):
                company_map[key] = comp

    items = []
    for link in links:
        company = company_map.get(str(link.company_id))
        items.append({
            "id": str(link.id),
            "user_id": str(link.user_id),
            "company_id": str(link.company_id),
            "company_name": company.name if company else None,
            "link_type": link.link_type,
        })
    return items


@router.post("/{user_id}/company-links")
async def add_company_link(
    user_id: str,
    payload: CompanyLinkCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("users")),
):
    link_type = payload.link_type
    company_id = str(payload.company_id)
    if link_type not in {"leader", "employee", "customer"}:
        raise HTTPException(status_code=400, detail="Invalid link_type")
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is required")

    user = await User.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    company = await Company.get_by_id(db, company_id)
    if not company:
        variants = _uuid_variants(company_id)
        if variants:
            comp_result = await db.execute(select(Company).where(Company.id.in_(variants)))
            company = comp_result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if link_type == "customer" and str(company.type or "") != "customer":
        raise HTTPException(status_code=400, detail="Customer link is allowed only for customer companies")

    existing = await db.execute(
        select(CompanyUserLink).where(
            CompanyUserLink.user_id == str(user.id),
            CompanyUserLink.company_id.in_(_uuid_variants(company.id)),
            CompanyUserLink.link_type == link_type,
        )
    )
    link = existing.scalar_one_or_none()
    if link:
        return {
            "id": str(link.id),
            "user_id": str(link.user_id),
            "company_id": str(link.company_id),
            "company_name": company.name,
            "link_type": link.link_type,
        }

    link = CompanyUserLink(
        company_id=str(company.id),
        user_id=str(user.id),
        link_type=link_type,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return {
        "id": str(link.id),
        "user_id": str(link.user_id),
        "company_id": str(link.company_id),
        "company_name": company.name,
        "link_type": link.link_type,
    }


@router.delete("/{user_id}/company-links/{link_id}")
async def delete_company_link(
    user_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("users")),
):
    user = await User.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(CompanyUserLink).where(
            CompanyUserLink.id == str(link_id),
            CompanyUserLink.user_id == str(user.id),
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.execute(delete(CompanyUserLink).where(CompanyUserLink.id == str(link_id)))
    await db.commit()
    return {"message": "Link deleted"}


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("users")),
):
    existing = await User.get_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    role_uuid = None
    if user.role_id:
        role_uuid = _parse_uuid(user.role_id, "role_id")
        role = await Role.get_by_id(db, role_uuid)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role.is_system and not bool(getattr(request.state, "is_superuser", False)):
            raise HTTPException(status_code=403, detail="Назначение системной роли разрешено только системному суперпользователю.")
    password_hash = hash_password(user.password)
    new_user = await User.create(
        db,
        email=user.email,
        full_name=user.full_name,
        role_id=str(role_uuid) if role_uuid else None,
        is_active=user.is_active,
        password_hash=password_hash,
    )
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("users")),
):
    existing_user = await User.get_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = payload.dict(exclude_unset=True)
    if "role_id" in update_data and update_data["role_id"]:
        role_uuid = _parse_uuid(update_data["role_id"], "role_id")
        role = await Role.get_by_id(db, role_uuid)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role.is_system and not bool(getattr(request.state, "is_superuser", False)):
            raise HTTPException(status_code=403, detail="Назначение системной роли разрешено только системному суперпользователю.")
        update_data["role_id"] = str(role_uuid)
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = hash_password(update_data["password"])
        update_data.pop("password", None)
    user = await User.update(db, user_id, **update_data)
    role_changed = "role_id" in update_data and str(existing_user.role_id or "") != str(user.role_id or "")
    deactivated = ("is_active" in update_data) and (not bool(user.is_active))
    if role_changed or deactivated:
        await revoke_user_tokens(str(user.id))
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_section_write("users")),
):
    user = await User.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    success = await User.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await revoke_user_tokens(str(user_id))
    return {"message": "User deleted"}
