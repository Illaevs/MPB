"""Pydantic-схемы для расширенной карточки сотрудника + отсутствий."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---- Profile -------------------------------------------------------------

class UserProfileBase(BaseModel):
    # Формальные поля — правит только админ.
    job_title: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    # Личные — правит сам пользователь или админ.
    birth_date: Optional[date] = None
    birth_show_year: bool = True
    bio: Optional[str] = Field(default=None, max_length=4000)
    interests: List[str] = []
    skills: List[str] = []
    telegram_username: Optional[str] = Field(default=None, max_length=64)

    @field_validator("interests", "skills", mode="before")
    @classmethod
    def _coerce_list(cls, v):
        # JSON-поле может прилететь из БД как None — нормализуем.
        if v is None:
            return []
        if isinstance(v, str):
            # На всякий случай: если кто-то залил строку.
            return [v]
        return list(v)

    @field_validator("telegram_username")
    @classmethod
    def _strip_at(cls, v):
        if not v:
            return v
        s = str(v).strip()
        if s.startswith("@"):
            s = s[1:]
        return s or None


class UserProfileResponse(UserProfileBase):
    """Полный профиль для вывода. Если `birth_show_year=False` — год
    в `birth_date` уже занулён бэком (см. router)."""
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    # Опциональные «снимки» полей для удобства фронта.
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role_name: Optional[str] = None
    manager_full_name: Optional[str] = None
    # Метаданные.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfilePatchSelf(BaseModel):
    """Что можно править САМОМУ. Формальные поля сюда не входят."""
    birth_date: Optional[date] = None
    birth_show_year: Optional[bool] = None
    bio: Optional[str] = Field(default=None, max_length=4000)
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    telegram_username: Optional[str] = Field(default=None, max_length=64)

    @field_validator("telegram_username")
    @classmethod
    def _strip_at_self(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if s.startswith("@"):
            s = s[1:]
        return s or None


class UserProfilePatchAdmin(UserProfilePatchSelf):
    """Админ может править всё."""
    job_title: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None


# ---- Absences ------------------------------------------------------------

ABSENCE_TYPES = ("vacation", "sick_leave", "business_trip", "other")


class AbsenceBase(BaseModel):
    type: str
    date_from: date
    date_to: date
    comment: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("type")
    @classmethod
    def _type_in_enum(cls, v):
        if v not in ABSENCE_TYPES:
            raise ValueError(
                f"type must be one of {ABSENCE_TYPES}, got {v!r}"
            )
        return v


class AbsenceCreate(AbsenceBase):
    # Необязательное: админ может создать чужую запись. Если пусто —
    # создаётся «свою».
    user_id: Optional[str] = None


class AbsencePatch(BaseModel):
    type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    comment: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("type")
    @classmethod
    def _type_in_enum_opt(cls, v):
        if v is None:
            return v
        if v not in ABSENCE_TYPES:
            raise ValueError(
                f"type must be one of {ABSENCE_TYPES}, got {v!r}"
            )
        return v


class AbsenceResponse(AbsenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    user_full_name: Optional[str] = None
    created_by: Optional[str] = None
    created_by_full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
