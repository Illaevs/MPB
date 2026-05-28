"""
Pydantic schemas for User model.
"""
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_serializer, field_validator

from app.services.user_avatar_bootstrap import avatars_root


def _resolve_avatar_filename(user_id: Union[str, UUID, None], avatar_url: Optional[str]) -> Optional[str]:
    if not avatar_url:
        return None
    root = avatars_root()
    raw_url = str(avatar_url).split("?", 1)[0]
    filename = Path(raw_url).name
    if filename:
        exact = root / filename
        try:
            exact.resolve().relative_to(root.resolve())
        except Exception:
            exact = None
        if exact and exact.exists() and exact.is_file():
            return exact.name

    user_key = str(user_id or "").strip()
    if not user_key:
        return None
    variants = {user_key}
    try:
        parsed = UUID(user_key)
        variants.add(parsed.hex)
        variants.add(str(parsed))
    except (ValueError, TypeError):
        if len(user_key) == 32:
            try:
                variants.add(str(UUID(hex=user_key)))
            except (ValueError, TypeError):
                pass
    candidates = []
    for variant in variants:
        candidates.extend([path for path in root.glob(f"{variant}-*") if path.is_file()])
    candidates = list({str(path): path for path in candidates}.values())
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0].name


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role_id: Optional[Union[str, UUID]] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value or "") < 10:
            raise ValueError("Пароль должен содержать не менее 10 символов.")
        if not re.search(r"[A-ZА-Я]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r"[a-zа-я]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        return value


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[Union[str, UUID]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return UserCreate.validate_password(value)


class CompanyLinkCreate(BaseModel):
    company_id: Union[str, UUID]
    link_type: str


class UserResponse(UserBase):
    id: Union[str, UUID]
    avatar_url: Optional[str] = None
    two_factor_enabled: Optional[bool] = False
    two_factor_enabled_at: Optional[datetime] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_serializer("avatar_url")
    def serialize_avatar_url(self, value):
        filename = _resolve_avatar_filename(self.id, value)
        if not filename:
            return None
        return f"/api/v1/users/avatar-user/{self.serialize_id(self.id)}"
