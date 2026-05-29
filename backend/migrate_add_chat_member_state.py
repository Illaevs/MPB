"""Идемпотентная миграция: добавить per-user state в chat_conversation_members.

Stage 1 плана `plans/messenger-implicit-dm.md`:
    - last_read_at DATETIME nullable   — для unread-счётчика
    - is_archived  BOOLEAN NOT NULL DEFAULT 0 — скрыть чат у себя
    - muted_until  DATETIME nullable   — заглушить уведомления до момента

Запуск:
  python backend/migrate_add_chat_member_state.py
DB-путь — из SQLALCHEMY_DATABASE_URI; абсолютные SQLite пути
(`sqlite:////path/...`) обрабатываются корректно (см. фикс
migrate_add_file_folder_permissions.py).
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

    # См. комментарий в migrate_add_file_folder_permissions.py: три случая.
    raw = uri.split("sqlite:///", 1)[1]
    is_windows_abs = len(raw) >= 2 and raw[1] == ":"
    is_unix_abs = raw.startswith("/")
    if is_unix_abs or is_windows_abs:
        path = raw
    else:
        path = str((Path(__file__).resolve().parent.parent / raw))

    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()
    changed: list[str] = []

    # Получаем текущие колонки.
    cur.execute("PRAGMA table_info(chat_conversation_members)")
    existing = {row[1] for row in cur.fetchall()}

    if not existing:
        print("table chat_conversation_members not found — nothing to migrate")
        con.close()
        return 4

    if "last_read_at" not in existing:
        cur.execute(
            "ALTER TABLE chat_conversation_members ADD COLUMN last_read_at DATETIME"
        )
        changed.append("col:last_read_at")

    if "is_archived" not in existing:
        # SQLite не поддерживает default expression на ALTER ADD COLUMN с
        # constraint NOT NULL без DEFAULT literal — используем 0.
        cur.execute(
            "ALTER TABLE chat_conversation_members "
            "ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"
        )
        changed.append("col:is_archived")

    if "muted_until" not in existing:
        cur.execute(
            "ALTER TABLE chat_conversation_members ADD COLUMN muted_until DATETIME"
        )
        changed.append("col:muted_until")

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
