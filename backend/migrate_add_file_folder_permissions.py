"""Идемпотентная миграция: создать таблицу file_folder_permissions.

Используется per-folder ACL для Files Catalog (см.
docs/plan: files-catalog-folder-acl). Таблица начинает пустой; правила
заводятся через UI или роутером при mkdir (creator-as-manager).

Запуск:
  python backend/migrate_add_file_folder_permissions.py
DB-путь — из SQLALCHEMY_DATABASE_URI.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Make `from app...` imports work when run from repo root or backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402


def main() -> int:
    uri = settings.SQLALCHEMY_DATABASE_URI
    if not uri.startswith("sqlite"):
        print(f"unsupported DB URI for this migration: {uri}")
        return 2
    path = uri.split("sqlite:///", 1)[1]
    path = path.lstrip("/")
    if not path.startswith(("/", "\\")) and len(path) >= 2 and path[1] != ":":
        path = str((Path(__file__).resolve().parent.parent / path))
    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()
    changed: list[str] = []

    # 1) Создать таблицу, если её ещё нет.
    cur.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table' AND name='file_folder_permissions'
        """
    )
    if cur.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE file_folder_permissions (
                id VARCHAR(36) PRIMARY KEY,
                folder_path VARCHAR(2000) NOT NULL,
                principal_type VARCHAR(16) NOT NULL,
                principal_id VARCHAR(36) NOT NULL,
                can_read BOOLEAN NOT NULL DEFAULT 0,
                can_write BOOLEAN NOT NULL DEFAULT 0,
                can_delete BOOLEAN NOT NULL DEFAULT 0,
                can_manage_perms BOOLEAN NOT NULL DEFAULT 0,
                inherit_to_subfolders BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id VARCHAR(36) NOT NULL,
                updated_at DATETIME,
                CONSTRAINT uq_ffp_unique_rule UNIQUE (folder_path, principal_type, principal_id),
                FOREIGN KEY (created_by_user_id) REFERENCES users (id)
            )
            """
        )
        changed.append("table:file_folder_permissions")

    # 2) Индексы (CREATE INDEX IF NOT EXISTS — идемпотентно).
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ffp_folder_path
            ON file_folder_permissions (folder_path)
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ffp_principal
            ON file_folder_permissions (principal_type, principal_id)
        """
    )
    # Уникальный индекс под constraint уже создан вместе с таблицей.

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
