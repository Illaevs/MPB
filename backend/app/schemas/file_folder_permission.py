"""Pydantic-схемы для управления per-folder ACL.

Эти схемы используются роутером `routers/file_folder_permissions.py`
(будет добавлен в Этапе 3 плана). Сейчас они нужны как контракт для
сервисов и фронта.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


PrincipalType = Literal["user", "role"]


class FolderPermissionFlags(BaseModel):
    """Четыре булевых флага. Используются как input в upsert и
    как часть output. По умолчанию все False — клиент явно ставит
    те, что должен дать.
    """

    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_manage_perms: bool = False


class FolderPermissionUpsert(FolderPermissionFlags):
    """Тело POST для создания/обновления правила. Идемпотентно по
    UniqueConstraint (folder_path, principal_type, principal_id) —
    повторный POST обновляет.
    """

    folder_path: str = Field(..., min_length=1, max_length=2000)
    principal_type: PrincipalType
    principal_id: str = Field(..., min_length=1, max_length=36)
    inherit_to_subfolders: bool = True

    @field_validator("folder_path")
    @classmethod
    def _validate_path(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("folder_path не может быть пустым")
        return v


class FolderPermissionRule(BaseModel):
    """Полный output: правило как оно лежит в БД, плюс читаемое имя
    принципала (резолвится роутером через JOIN с users/roles).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    folder_path: str
    principal_type: PrincipalType
    principal_id: str
    # Удобство для UI — отдаём вместе с правилом, чтобы не делать
    # отдельный запрос. Резолвится в роутере.
    principal_label: Optional[str] = None
    principal_avatar_url: Optional[str] = None

    can_read: bool
    can_write: bool
    can_delete: bool
    can_manage_perms: bool
    inherit_to_subfolders: bool

    created_at: datetime
    created_by_user_id: str
    updated_at: Optional[datetime] = None

    # Где правило задано относительно текущей просматриваемой папки.
    # 'explicit' — на этой же папке; 'inherited' — на предке.
    # source_path — folder_path предка (для лейбла «← из /Архив/2026/»).
    source_kind: Literal["explicit", "inherited"] = "explicit"
    source_path: Optional[str] = None


class FolderPermissionsResponse(BaseModel):
    """Структура ответа GET /api/v1/files-catalog/permissions?path=...

    `effective_for_me` — что текущий пользователь в итоге может с этой
    папкой делать. Удобно для фронта (показать сразу «у вас доступ X»).
    """

    folder_path: str
    is_entity_path: bool = Field(
        ..., description=(
            "True для папок под /deals/, /contracts/ и др. — на них "
            "per-folder ACL не действует, управлять правами нельзя."
        )
    )
    explicit: List[FolderPermissionRule] = []
    inherited: List[FolderPermissionRule] = []
    effective_for_me: FolderPermissionFlags
