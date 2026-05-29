"""FileFolderPermission — per-folder ACL для Files Catalog.

Одна строка = правило доступа `(folder_path, principal)` → 4 флага +
управление наследованием. Папки под зарезервированными префиксами
сущностей (`/deals/...`, `/contracts/...`, ...) обходят эту таблицу —
для них действует path-based authz через `services/storage_authz.py`.

Создатель папки автоматически получает строку с `can_manage_perms=True`
и `inherit_to_subfolders=False` при первом mkdir (вставка делается в
самом роутере files_catalog при создании каталога). Это даёт
самодокументируемую запись о владельце и работает через тот же
механизм резолва, без отдельной таблицы folder_meta.

Резолв effective_perms — в `services/folder_acl.py` (request-scoped
кэш, чтобы при глубоком листинге не ходить в БД повторно).
"""
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database.base import Base


# Допустимые значения principal_type. Перечень намеренно узкий: расширять
# только осознанно (например, "org_unit" в будущем).
PRINCIPAL_TYPE_USER = "user"
PRINCIPAL_TYPE_ROLE = "role"
ALLOWED_PRINCIPAL_TYPES = (PRINCIPAL_TYPE_USER, PRINCIPAL_TYPE_ROLE)


class FileFolderPermission(Base):
    __tablename__ = "file_folder_permissions"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Нормализованный путь:
    #   - всегда начинается с '/';
    #   - всегда заканчивается '/' (это папка, а не файл);
    #   - корень — '/';
    #   - сегменты как у storage (UTF-8, lowercase не обязательно).
    # См. folder_acl.normalize_path() — единственное место нормализации.
    folder_path = Column(String(2000), nullable=False)

    # 'user' | 'role'. См. константы выше.
    principal_type = Column(String(16), nullable=False)
    # ID пользователя или роли. FK не ставим (две разных целевых таблицы);
    # консистентность обеспечивается на уровне роутера + миграции CASCADE.
    principal_id = Column(String(36), nullable=False)

    # Гранулярность прав. Все четыре — обычные BOOLEAN; одно правило может
    # давать любую комбинацию. Отсутствие правила = ничего.
    can_read = Column(Boolean, nullable=False, default=False)
    can_write = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
    can_manage_perms = Column(Boolean, nullable=False, default=False)

    # True (дефолт): правило применяется и к подпапкам рекурсивно.
    # False: правило действует только на эту конкретную папку.
    # На MVP «прервать наследование» отдельно НЕ реализовано; для
    # «доступ только сюда, без подпапок» используем inherit=False.
    inherit_to_subfolders = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Автор правила: superuser, создатель папки или владелец manage_perms
    # на родительском уровне (см. роутер file_folder_permissions).
    created_by_user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        # Одно правило на (папка, принципал). Если хотим обновить —
        # делаем UPDATE, а не INSERT нового. Гарантия в БД.
        UniqueConstraint(
            "folder_path",
            "principal_type",
            "principal_id",
            name="uq_ffp_unique_rule",
        ),
        # Для запроса всех правил по пути (effective_perms) — главный путь
        # читает по этому индексу.
        Index("ix_ffp_folder_path", "folder_path"),
        # Для запросов «где у user/role есть права» (UI «мои папки»,
        # аудит).
        Index("ix_ffp_principal", "principal_type", "principal_id"),
    )

    @property
    def perm_flags(self) -> set:
        """Конвертирует 4 BOOLEAN в set, удобный для logic-операций."""
        from app.services.folder_acl import Perm  # локальный импорт — нет цикла

        out: set = set()
        if self.can_read:
            out.add(Perm.READ)
        if self.can_write:
            out.add(Perm.WRITE)
        if self.can_delete:
            out.add(Perm.DELETE)
        if self.can_manage_perms:
            out.add(Perm.MANAGE)
        return out
