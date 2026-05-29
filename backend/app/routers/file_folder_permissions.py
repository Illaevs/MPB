"""Управление per-folder ACL для Files Catalog.

3 эндпоинта — Stage 3 плана plans/files-catalog-folder-acl.md:

- GET    /api/v1/files-catalog/permissions?path=<folder>
  Возвращает explicit + inherited правила + effective_for_me.
- POST   /api/v1/files-catalog/permissions
  Идемпотентный upsert по UniqueConstraint (folder_path, principal_type,
  principal_id).
- DELETE /api/v1/files-catalog/permissions/{id}
  Удалить конкретное правило по id.

Все три эндпоинта требуют MANAGE на `folder_path`. Это проверяется
через `require_folder_perm` — суперюзер обходит, владелец папки имеет
MANAGE автоматически (см. `grant_creator_manage_perms`).

Под entity-paths (`/deals/`, `/contracts/`, ...) per-folder ACL
выключен — POST вернёт 400, GET — пустой ответ с флагом
`is_entity_path=True`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import Role, User
from app.models.file_folder_permission import (
    ALLOWED_PRINCIPAL_TYPES,
    FileFolderPermission,
    PRINCIPAL_TYPE_ROLE,
    PRINCIPAL_TYPE_USER,
)
from app.schemas.file_folder_permission import (
    FolderPermissionFlags,
    FolderPermissionRule,
    FolderPermissionUpsert,
    FolderPermissionsResponse,
)
from app.services.audit_log import create_audit_log
from app.services.event_outbox import emit_event_safe
from app.services.folder_acl import (
    Perm,
    effective_perms,
    is_entity_path,
    normalize_path,
    path_ancestors,
    require_folder_perm,
)


router = APIRouter()


# ────────────────────────────────────────────────────────────────────
# helpers: snapshot правила (для AuditLog before/after + payload эмита)
# ────────────────────────────────────────────────────────────────────


def _rule_snapshot(rule: FileFolderPermission) -> dict:
    """Сериализация правила в dict для payload эмита и AuditLog.

    Минимально достаточный набор: чтобы по строке аудита можно было
    восстановить «кому и какие флаги были даны/убраны».
    """
    return {
        "id": str(rule.id),
        "folder_path": rule.folder_path,
        "principal_type": rule.principal_type,
        "principal_id": str(rule.principal_id),
        "flags": {
            "can_read": bool(rule.can_read),
            "can_write": bool(rule.can_write),
            "can_delete": bool(rule.can_delete),
            "can_manage_perms": bool(rule.can_manage_perms),
        },
        "inherit_to_subfolders": bool(rule.inherit_to_subfolders),
    }


# ────────────────────────────────────────────────────────────────────
# helpers: principal labels (user.full_name / role.name)
# ────────────────────────────────────────────────────────────────────


async def _resolve_principal_labels(
    db: AsyncSession,
    rules: list[FileFolderPermission],
) -> dict[tuple[str, str], tuple[Optional[str], Optional[str]]]:
    """Достаёт (label, avatar_url) для каждой пары (principal_type,
    principal_id), упомянутой в правилах.

    Возвращает словарь:
        { (principal_type, principal_id): (label, avatar_url) }

    Делаем по одному SELECT на каждый тип принципала — это два запроса
    против количество рулов × N запросов.
    """
    user_ids: set[str] = set()
    role_ids: set[str] = set()
    for r in rules:
        if r.principal_type == PRINCIPAL_TYPE_USER:
            user_ids.add(str(r.principal_id))
        elif r.principal_type == PRINCIPAL_TYPE_ROLE:
            role_ids.add(str(r.principal_id))

    labels: dict[tuple[str, str], tuple[Optional[str], Optional[str]]] = {}

    if user_ids:
        urows = (
            await db.execute(
                select(User.id, User.full_name, User.avatar_url).where(
                    User.id.in_(list(user_ids))
                )
            )
        ).all()
        for uid, full_name, avatar_url in urows:
            labels[(PRINCIPAL_TYPE_USER, str(uid))] = (full_name, avatar_url)

    if role_ids:
        rrows = (
            await db.execute(
                select(Role.id, Role.name).where(Role.id.in_(list(role_ids)))
            )
        ).all()
        for rid, name in rrows:
            labels[(PRINCIPAL_TYPE_ROLE, str(rid))] = (name, None)

    return labels


def _rule_to_schema(
    rule: FileFolderPermission,
    labels: dict[tuple[str, str], tuple[Optional[str], Optional[str]]],
    *,
    source_kind: str = "explicit",
    source_path: Optional[str] = None,
) -> FolderPermissionRule:
    """Сериализация ORM → Pydantic. source_kind/source_path заполняются
    наружно (GET-эндпоинт знает, на какой папке смотрят и откуда правило
    пришло — explicit или inherited)."""
    key = (rule.principal_type, str(rule.principal_id))
    label, avatar = labels.get(key, (None, None))
    return FolderPermissionRule(
        id=str(rule.id),
        folder_path=rule.folder_path,
        principal_type=rule.principal_type,
        principal_id=str(rule.principal_id),
        principal_label=label,
        principal_avatar_url=avatar,
        can_read=bool(rule.can_read),
        can_write=bool(rule.can_write),
        can_delete=bool(rule.can_delete),
        can_manage_perms=bool(rule.can_manage_perms),
        inherit_to_subfolders=bool(rule.inherit_to_subfolders),
        created_at=rule.created_at,
        created_by_user_id=str(rule.created_by_user_id),
        updated_at=rule.updated_at,
        source_kind=source_kind,
        source_path=source_path,
    )


# ────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────


@router.get(
    "/files-catalog/permissions",
    response_model=FolderPermissionsResponse,
)
async def list_folder_permissions(
    request: Request,
    path: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Возвращает explicit + inherited правила и effective_for_me.

    Для entity-paths возвращает пустой ответ с `is_entity_path=True`.
    """
    norm = normalize_path(path)

    # Effective для текущего юзера — отдаём вместе со списком, чтобы UI
    # сразу мог нарисовать «у вас есть Read/Write/...» без отдельного
    # запроса. Делаем это ДО гейта по MANAGE — суть в том, что увидеть
    # СВОИ права может любой авторизованный, а вот менять правила —
    # только MANAGE.
    my_perms = await effective_perms(db, user, norm, request=request)
    effective_flags = FolderPermissionFlags(
        can_read=Perm.READ in my_perms,
        can_write=Perm.WRITE in my_perms,
        can_delete=Perm.DELETE in my_perms,
        can_manage_perms=Perm.MANAGE in my_perms,
    )

    if is_entity_path(norm):
        # Per-folder ACL отключён; UI просто не покажет «Управление
        # доступом» для таких папок.
        return FolderPermissionsResponse(
            folder_path=norm,
            is_entity_path=True,
            explicit=[],
            inherited=[],
            effective_for_me=effective_flags,
        )

    # Гейтим просмотр списка правил по MANAGE на этой папке.
    await require_folder_perm(db, user, norm, Perm.MANAGE, request=request)

    # explicit: правила, у которых folder_path == norm.
    # inherited: правила на предках с inherit_to_subfolders=True.
    ancestors = path_ancestors(norm)
    parents_only = [p for p in ancestors if p != norm]

    explicit_rules: list[FileFolderPermission] = []
    inherited_rules: list[FileFolderPermission] = []

    if ancestors:
        stmt = (
            select(FileFolderPermission)
            .where(FileFolderPermission.folder_path.in_(ancestors))
            .where(
                or_(
                    FileFolderPermission.folder_path == norm,
                    FileFolderPermission.inherit_to_subfolders.is_(True),
                )
            )
        )
        rows = (await db.execute(stmt)).scalars().all()
        for r in rows:
            if r.folder_path == norm:
                explicit_rules.append(r)
            elif r.folder_path in parents_only and r.inherit_to_subfolders:
                inherited_rules.append(r)

    # Достаём labels одним блоком для всех (user + role) принципалов.
    labels = await _resolve_principal_labels(
        db, explicit_rules + inherited_rules
    )

    return FolderPermissionsResponse(
        folder_path=norm,
        is_entity_path=False,
        explicit=[
            _rule_to_schema(r, labels, source_kind="explicit", source_path=norm)
            for r in explicit_rules
        ],
        inherited=[
            _rule_to_schema(
                r, labels, source_kind="inherited", source_path=r.folder_path
            )
            for r in inherited_rules
        ],
        effective_for_me=effective_flags,
    )


@router.post(
    "/files-catalog/permissions",
    response_model=FolderPermissionRule,
)
async def upsert_folder_permission(
    payload: FolderPermissionUpsert,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать/обновить правило. Идемпотентно по уникальному ключу
    (folder_path, principal_type, principal_id).

    Валидация:
      - путь не entity-path;
      - principal_type корректный;
      - principal_id существует в соответствующей таблице (User/Role);
      - вызывающий имеет MANAGE на folder_path.
    """
    norm = normalize_path(payload.folder_path)

    if is_entity_path(norm):
        raise HTTPException(
            status_code=400,
            detail=(
                "Per-folder ACL не применим к entity-path "
                "(/deals/, /contracts/, ...). Управляйте доступом через "
                "соответствующую сущность."
            ),
        )

    if payload.principal_type not in ALLOWED_PRINCIPAL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown principal_type: {payload.principal_type}",
        )

    # Проверяем существование принципала. Если фронт передал случайный
    # UUID, мы скажем 400 здесь, а не оставим orphan-строку в БД.
    if payload.principal_type == PRINCIPAL_TYPE_USER:
        exists = (
            await db.execute(
                select(User.id).where(User.id == payload.principal_id)
            )
        ).scalar_one_or_none()
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"User {payload.principal_id} not found",
            )
    elif payload.principal_type == PRINCIPAL_TYPE_ROLE:
        exists = (
            await db.execute(
                select(Role.id).where(Role.id == payload.principal_id)
            )
        ).scalar_one_or_none()
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Role {payload.principal_id} not found",
            )

    # Гейт MANAGE.
    await require_folder_perm(db, user, norm, Perm.MANAGE, request=request)

    # Upsert: ищем существующее, если есть — апдейтим, иначе создаём.
    existing = (
        await db.execute(
            select(FileFolderPermission).where(
                and_(
                    FileFolderPermission.folder_path == norm,
                    FileFolderPermission.principal_type == payload.principal_type,
                    FileFolderPermission.principal_id == payload.principal_id,
                )
            )
        )
    ).scalar_one_or_none()

    is_create = existing is None
    before_snapshot = None
    if existing:
        before_snapshot = _rule_snapshot(existing)
        existing.can_read = payload.can_read
        existing.can_write = payload.can_write
        existing.can_delete = payload.can_delete
        existing.can_manage_perms = payload.can_manage_perms
        existing.inherit_to_subfolders = payload.inherit_to_subfolders
        rule = existing
    else:
        rule = FileFolderPermission(
            folder_path=norm,
            principal_type=payload.principal_type,
            principal_id=payload.principal_id,
            can_read=payload.can_read,
            can_write=payload.can_write,
            can_delete=payload.can_delete,
            can_manage_perms=payload.can_manage_perms,
            inherit_to_subfolders=payload.inherit_to_subfolders,
            created_by_user_id=str(user.id),
        )
        db.add(rule)

    # flush — чтобы rule.id появился до эмита и попал в outbox.entity_id.
    await db.flush()
    after_snapshot = _rule_snapshot(rule)

    # Event Bus: created / updated. payload содержит «итоговое» состояние;
    # для updated дополнительно кладём before для удобства подписчика.
    # Раздельные ветки — чтобы autogen-каталог (app.tools.dump_event_types)
    # увидел оба event_type как литералы.
    emit_payload = {
        **after_snapshot,
        "actor_user_id": str(user.id),
        "source": "explicit",
    }
    if before_snapshot is not None:
        emit_payload["before"] = before_snapshot

    if is_create:
        outbox = await emit_event_safe(
            db,
            event_type="file_folder_permission.created",
            entity_type="file_folder_permission",
            entity_id=str(rule.id),
            payload=emit_payload,
            payload_version=1,
        )
    else:
        outbox = await emit_event_safe(
            db,
            event_type="file_folder_permission.updated",
            entity_type="file_folder_permission",
            entity_id=str(rule.id),
            payload=emit_payload,
            payload_version=1,
        )

    await db.commit()
    await db.refresh(rule)

    # AuditLog. Делает свой commit, но к этому моменту outbox-row уже
    # закоммичен — оба окажутся в БД, последовательно.
    await create_audit_log(
        db,
        entity_type="file_folder_permission",
        entity_id=str(rule.id),
        action="permission_granted" if is_create else "permission_updated",
        user_id=str(user.id),
        before=before_snapshot,
        after=after_snapshot,
        meta={
            "folder_path": rule.folder_path,
            "principal_type": rule.principal_type,
            "principal_id": str(rule.principal_id),
            "source": "explicit",
        },
        source_event_id=outbox.event_id if outbox else None,
    )

    labels = await _resolve_principal_labels(db, [rule])
    return _rule_to_schema(rule, labels, source_kind="explicit", source_path=norm)


@router.delete("/files-catalog/permissions/{rule_id}")
async def delete_folder_permission(
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить конкретное правило. MANAGE проверяется на той же папке,
    к которой относится правило (не на той, где сейчас находится UI)."""
    rule = (
        await db.execute(
            select(FileFolderPermission).where(
                FileFolderPermission.id == rule_id
            )
        )
    ).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Permission rule not found")

    await require_folder_perm(
        db, user, rule.folder_path, Perm.MANAGE, request=request
    )

    # Снимок ДО удаления — пригодится и в payload, и в AuditLog.before.
    snapshot = _rule_snapshot(rule)
    folder_path = rule.folder_path

    await db.delete(rule)

    outbox = await emit_event_safe(
        db,
        event_type="file_folder_permission.deleted",
        entity_type="file_folder_permission",
        entity_id=str(rule_id),
        payload={
            **snapshot,
            "actor_user_id": str(user.id),
        },
        payload_version=1,
    )

    await db.commit()

    await create_audit_log(
        db,
        entity_type="file_folder_permission",
        entity_id=str(rule_id),
        action="permission_revoked",
        user_id=str(user.id),
        before=snapshot,
        meta={
            "folder_path": folder_path,
            "principal_type": snapshot["principal_type"],
            "principal_id": snapshot["principal_id"],
        },
        source_event_id=outbox.event_id if outbox else None,
    )

    return {"deleted": True, "id": rule_id}
