"""Резолв per-folder ACL для Files Catalog (см. models.file_folder_permission).

Этот модуль НЕ владеет общим path-authz для папок под сущностями
(`/deals/{id}/...`, `/contracts/{id}/...`, ...). Для них есть отдельный
`services/storage_authz.py`, и `effective_perms()` делегирует туда — мы
не дублируем логику и не позволяем per-folder правилам подменить
бизнес-ACL по сущности.

Базовая идея резолва:
  1. Если путь — под зарезервированным entity-префиксом → отдаём
     стандартный path-ACL (storage_authz). Per-folder правила тут
     НЕ применяются (продуктовое решение).
  2. Если пользователь — superuser → все 4 пермиссии всегда.
  3. Иначе собираем все правила с принципалами = (user_id) или
     (role_id), у которых folder_path является префиксом target и
     (inherit_to_subfolders == True ИЛИ folder_path == target).
  4. Объединяем флаги: правила АДДИТИВНЫ. На MVP «явный deny» в
     подпапке не реализован — структурой папок надо моделировать
     различия в доступе через NOT-grant вместо deny.
  5. Если правил нет — фолбэк на section_permissions (files_catalog):
       read_all → {READ, WRITE, DELETE}  (без MANAGE — manage только
         через явное правило или superuser);
       read_assigned → {READ};
       нет прав → {}.

Кэш: на уровне FastAPI Request (через `request.state`). При одном
HTTP-запросе листинг папки + проверки на каждый item не должны
ходить в БД по нескольку раз.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional, Set

from fastapi import HTTPException, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_folder_permission import (
    ALLOWED_PRINCIPAL_TYPES,
    FileFolderPermission,
    PRINCIPAL_TYPE_ROLE,
    PRINCIPAL_TYPE_USER,
)
from app.models.user import User


# Папки под этими префиксами не подчиняются per-folder ACL —
# их видимость определяется доступом к сущности (сделке/договору/...).
# Список фиксированный: совпадает с storage_authz._ENTITY_PREFIXES.
# Если добавляем новый entity-mounted раздел в storage_authz —
# обязательно дублируем сюда.
ENTITY_PATH_PREFIXES = (
    "/deals/",
    "/contracts/",
    "/legal-work/",
    "/legal_work/",
    "/customer/",
    "/executor/",
    "/subcontractor/",
    "/subcontractors/",
    "/outgoing/",
    "/_tasks/",
    # Системные папки вложений: мессенджер и чат задач. Доступ к ним
    # управляется ACL мессенджера/задач, НЕ per-folder ACL каталога.
    # Без этого permissions-эндпоинт требует MANAGE и валит ложный 403
    # при просмотре каталога (видны как обычные папки).
    "/_chat/",
    "/_task_chat/",
)


class Perm(str, Enum):
    """Гранулярные пермиссии на папку. См. модель — 4 BOOLEAN."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage_perms"


ALL_PERMS: Set[Perm] = {Perm.READ, Perm.WRITE, Perm.DELETE, Perm.MANAGE}


# ────────────────────────────────────────────────────────────────────
# Нормализация пути
# ────────────────────────────────────────────────────────────────────


def normalize_path(p: Optional[str]) -> str:
    """Приводит путь к каноническому виду для FFP.

    Правила:
      - None / пусто → '/'
      - заменяем backslash → '/' (Windows-friendly)
      - схлопываем повторные '/'
      - убираем '.' и '..' сегменты (защита от path traversal в логике
        резолва — даже если роутер пропустил)
      - всегда начинается с '/'
      - всегда заканчивается '/' (это путь к папке)

    Не пытаемся валидировать существование папки на диске — это не
    задача нормализации; effective_perms работает с любым «логически
    правильным» путём.
    """
    if not p:
        return "/"
    s = p.strip().replace("\\", "/")
    # Гарантируем ведущий '/'
    if not s.startswith("/"):
        s = "/" + s
    # Раскладываем сегменты, убирая '.' и '..'
    out_segments: list[str] = []
    for seg in s.split("/"):
        if not seg or seg == ".":
            continue
        if seg == "..":
            if out_segments:
                out_segments.pop()
            continue
        out_segments.append(seg)
    if not out_segments:
        return "/"
    return "/" + "/".join(out_segments) + "/"


def path_ancestors(folder_path: str) -> list[str]:
    """Список всех путей-предков нормализованного folder_path,
    включая корень '/' и сам путь.

    Пример:
      "/Архив/2026/01/" → ["/", "/Архив/", "/Архив/2026/", "/Архив/2026/01/"]

    Используется effective_perms для одного SQL `IN (...)`.
    """
    norm = normalize_path(folder_path)
    out = ["/"]
    if norm == "/":
        return out
    segments = norm.strip("/").split("/")
    acc = ""
    for seg in segments:
        acc += "/" + seg
        out.append(acc + "/")
    return out


def is_entity_path(folder_path: str) -> bool:
    """True, если путь попадает под зарезервированный entity-префикс.

    Корневой '/' — НЕ entity. Любая папка верхнего уровня вида
    '/deals/' (без id) — тоже не entity (это контейнер); только
    '/deals/{id}/...' считается entity-path и ходит через storage_authz.
    Для простоты MVP: проверяем строгое совпадение префикса.
    """
    norm = normalize_path(folder_path)
    return any(norm.startswith(prefix) for prefix in ENTITY_PATH_PREFIXES)


# ────────────────────────────────────────────────────────────────────
# Резолв effective_perms
# ────────────────────────────────────────────────────────────────────


def _request_cache(request: Optional[Request]) -> dict:
    """Возвращает (создавая при первом обращении) кэш на request.state.

    Если request не передан (например, вызов из service-слоя без HTTP-
    контекста), возвращаем одноразовый dict — без переиспользования.
    """
    if request is None:
        return {}
    cache = getattr(request.state, "_folder_acl_cache", None)
    if cache is None:
        cache = {}
        request.state._folder_acl_cache = cache
    return cache


async def _section_fallback(
    db: AsyncSession, user: User, section: str = "files_catalog"
) -> Set[Perm]:
    """Базовые права когда на пути НЕТ ни одного FFP-правила.

    Логика:
      read_all → {READ, WRITE, DELETE}  (MANAGE требует явного правила
        или superuser);
      read_assigned → {READ};
      нет прав → {}.

    Локальный импорт `get_section_permissions` — чтобы не создавать
    циклов import между services/.
    """
    from app.services.permissions import get_section_permissions

    read_all, read_assigned = await get_section_permissions(
        db, user.role_id, section
    )
    if read_all:
        return {Perm.READ, Perm.WRITE, Perm.DELETE}
    if read_assigned:
        return {Perm.READ}
    return set()


async def _entity_path_perms(
    db: AsyncSession, user: User, folder_path: str
) -> Set[Perm]:
    """Делегат для путей под сущностью.

    Сейчас storage_authz возвращает bool (есть доступ или нет). Мы
    интерпретируем «есть доступ» как {READ, WRITE, DELETE} (MANAGE
    не даём — управлять правами на entity-папки нельзя, см. продуктовое
    решение). «Нет доступа» → пустое множество.

    Если в будущем storage_authz станет возвращать гранулярные
    флаги — заменим маппинг.
    """
    from app.services.storage_authz import authorize_storage_path

    try:
        # authorize_storage_path кидает HTTPException при отказе.
        # Завернём в try/except — чтобы не пропускать 403 наружу
        # как побочный эффект effective_perms.
        await authorize_storage_path(db=db, user=user, path=folder_path)
        return {Perm.READ, Perm.WRITE, Perm.DELETE}
    except HTTPException:
        return set()
    except Exception:
        # Любой неожиданный сбой intentionally трактуем как «нет прав».
        # Это fail-closed по дизайну ACL.
        return set()


def _is_superuser(user: User) -> bool:
    """Признак суперпользователя — у нас несколько способов разметки;
    унифицирую в одном месте, чтобы не тянуть запрос про роль повсюду.
    """
    return bool(getattr(user, "is_superuser", False))


async def _query_matching_rules(
    db: AsyncSession,
    user: User,
    target_path: str,
) -> list[FileFolderPermission]:
    """Один SQL-запрос: все правила на пути target и его предках,
    у которых принципал — наш user или его role, с учётом
    inherit_to_subfolders.

    Поведение:
      - folder_path == target → правило применяется независимо от
        inherit_to_subfolders;
      - folder_path == один из предков target → применяется только если
        inherit_to_subfolders == True.

    Нюанс реализации: ограничение по «inherit или точное совпадение»
    выражается через OR в where; альтернативно можно тянуть всё и
    фильтровать в Python, но 21 предок × ~5 правил = ~100 строк —
    проще отфильтровать на стороне БД.
    """
    target_norm = normalize_path(target_path)
    ancestors = path_ancestors(target_norm)
    # Принципалы: user_id всегда; role_id — только если у юзера роль есть.
    principal_clauses = [
        and_(
            FileFolderPermission.principal_type == PRINCIPAL_TYPE_USER,
            FileFolderPermission.principal_id == str(user.id),
        )
    ]
    if user.role_id:
        principal_clauses.append(
            and_(
                FileFolderPermission.principal_type == PRINCIPAL_TYPE_ROLE,
                FileFolderPermission.principal_id == str(user.role_id),
            )
        )

    stmt = (
        select(FileFolderPermission)
        .where(FileFolderPermission.folder_path.in_(ancestors))
        .where(or_(*principal_clauses))
        .where(
            or_(
                FileFolderPermission.folder_path == target_norm,
                FileFolderPermission.inherit_to_subfolders.is_(True),
            )
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def effective_perms(
    db: AsyncSession,
    user: User,
    folder_path: str,
    *,
    request: Optional[Request] = None,
) -> Set[Perm]:
    """Эффективный набор пермиссий пользователя на папку.

    request — опциональный (для кэширования на уровне HTTP-запроса).
    Если None — кэширования нет (например, вызов из cron-таски).
    """
    norm = normalize_path(folder_path)
    cache = _request_cache(request)
    if norm in cache:
        return cache[norm]

    # 1) Entity path → специальная ветка через storage_authz.
    if is_entity_path(norm):
        result = await _entity_path_perms(db, user, norm)
        cache[norm] = result
        return result

    # 2) Superuser → всё, всегда.
    if _is_superuser(user):
        result = ALL_PERMS.copy()
        cache[norm] = result
        return result

    # 3) Свободная папка: собираем матчинг-правила и объединяем флаги.
    rules = await _query_matching_rules(db, user, norm)

    if rules:
        result: Set[Perm] = set()
        for r in rules:
            if r.can_read:
                result.add(Perm.READ)
            if r.can_write:
                result.add(Perm.WRITE)
            if r.can_delete:
                result.add(Perm.DELETE)
            if r.can_manage_perms:
                result.add(Perm.MANAGE)
    else:
        # 4) Нет ни одного применимого правила → section fallback.
        result = await _section_fallback(db, user)

    cache[norm] = result
    return result


async def require_folder_perm(
    db: AsyncSession,
    user: User,
    folder_path: str,
    perm: Perm,
    *,
    request: Optional[Request] = None,
) -> None:
    """Гард для роутеров: бросает HTTPException(403) если пермиссии нет.

    Использование в files_catalog:
        await require_folder_perm(db, user, path, Perm.WRITE, request=request)
    """
    eff = await effective_perms(db, user, folder_path, request=request)
    if perm not in eff:
        raise HTTPException(
            status_code=403,
            detail=f"No '{perm.value}' permission on folder {folder_path}",
        )


# ────────────────────────────────────────────────────────────────────
# Хелпер: правило «создатель → manage_perms» при mkdir
# ────────────────────────────────────────────────────────────────────


async def grant_creator_manage_perms(
    db: AsyncSession,
    user: User,
    folder_path: str,
) -> Optional[FileFolderPermission]:
    """Создаёт правило «принципал=создатель имеет все 4 флага только
    на этой папке (не на подпапках)».

    Вызывается из files_catalog.mkdir СРАЗУ после успешного создания
    папки. Идемпотентно по UniqueConstraint (folder_path, principal_type,
    principal_id) — если правило уже есть, ничего не делаем.

    Для entity-path не делает ничего — там per-folder ACL отключён.
    Для корня '/' тоже не делает (root никто не создаёт).
    """
    norm = normalize_path(folder_path)
    if norm == "/" or is_entity_path(norm):
        return None
    if _is_superuser(user):
        # У супера и так всё; не плодим формальных записей.
        return None

    # Проверяем что правила ещё нет.
    existing = (
        await db.execute(
            select(FileFolderPermission).where(
                and_(
                    FileFolderPermission.folder_path == norm,
                    FileFolderPermission.principal_type == PRINCIPAL_TYPE_USER,
                    FileFolderPermission.principal_id == str(user.id),
                )
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    rule = FileFolderPermission(
        folder_path=norm,
        principal_type=PRINCIPAL_TYPE_USER,
        principal_id=str(user.id),
        can_read=True,
        can_write=True,
        can_delete=True,
        can_manage_perms=True,
        inherit_to_subfolders=False,
        created_by_user_id=str(user.id),
    )
    db.add(rule)
    await db.flush()

    # Event Bus: эмитим creator-grant. Лежит в той же транзакции,
    # что и сам rule — каскадно закоммитится из mkdir. Если outbox
    # сломан, emit_event_safe тихо проглотит — mkdir не упадёт.
    try:
        from app.services.event_outbox import emit_event_safe

        await emit_event_safe(
            db,
            event_type="file_folder_permission.created",
            entity_type="file_folder_permission",
            entity_id=str(rule.id),
            payload={
                "id": str(rule.id),
                "folder_path": rule.folder_path,
                "principal_type": rule.principal_type,
                "principal_id": str(rule.principal_id),
                "flags": {
                    "can_read": True,
                    "can_write": True,
                    "can_delete": True,
                    "can_manage_perms": True,
                },
                "inherit_to_subfolders": False,
                "actor_user_id": str(user.id),
                "source": "creator_grant",
            },
            payload_version=1,
        )
    except Exception:  # pragma: no cover — defensive
        pass

    return rule


# ────────────────────────────────────────────────────────────────────
# Хелпер: каскадные операции при rename/move/delete папки
# ────────────────────────────────────────────────────────────────────


async def rename_folder_path_prefix(
    db: AsyncSession, old_prefix: str, new_prefix: str
) -> int:
    """Меняет folder_path во всех FFP-правилах, чьи пути начинаются с
    old_prefix, на new_prefix. Возвращает количество обновлённых строк.

    Вызывается при rename/move папки в files_catalog. Old и new — уже
    нормализованные.
    """
    old_norm = normalize_path(old_prefix)
    new_norm = normalize_path(new_prefix)
    if old_norm == new_norm:
        return 0

    # SQLite не поддерживает COALESCE/REPLACE в UPDATE с условием через
    # ORM-стандарт без хака. Используем raw-SQL через text() — это
    # один атомарный UPDATE.
    from sqlalchemy import text

    sql = text(
        """
        UPDATE file_folder_permissions
        SET folder_path = :new_prefix || substr(folder_path, length(:old_prefix) + 1),
            updated_at = CURRENT_TIMESTAMP
        WHERE folder_path = :old_prefix
           OR folder_path LIKE :old_prefix_like
        """
    )
    res = await db.execute(
        sql,
        {
            "new_prefix": new_norm,
            "old_prefix": old_norm,
            "old_prefix_like": old_norm + "%",
        },
    )
    return res.rowcount or 0


async def delete_folder_path_prefix(
    db: AsyncSession, prefix: str
) -> int:
    """Удаляет все FFP-правила для папки и её подпапок.

    Вызывается при delete папки в files_catalog. Возвращает количество
    удалённых строк.
    """
    from sqlalchemy import text

    norm = normalize_path(prefix)
    sql = text(
        """
        DELETE FROM file_folder_permissions
        WHERE folder_path = :prefix OR folder_path LIKE :prefix_like
        """
    )
    res = await db.execute(
        sql, {"prefix": norm, "prefix_like": norm + "%"}
    )
    return res.rowcount or 0


__all__ = [
    "Perm",
    "ALL_PERMS",
    "ENTITY_PATH_PREFIXES",
    "normalize_path",
    "path_ancestors",
    "is_entity_path",
    "effective_perms",
    "require_folder_perm",
    "grant_creator_manage_perms",
    "rename_folder_path_prefix",
    "delete_folder_path_prefix",
]
