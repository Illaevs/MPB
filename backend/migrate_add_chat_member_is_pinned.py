"""Идемпотентная миграция: добавить is_pinned в chat_conversation_members.

Phase B.1 плана messenger-implicit-dm:
    is_pinned BOOLEAN NOT NULL DEFAULT 0  — закрепить чат у себя
    (сортируется выше остальных в сайдбаре).

Запуск:
  python backend/migrate_add_chat_member_is_pinned.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402


def main() -> int:
    uri = settings.SQLALCHEMY_DATABASE_URI
    if not uri.startswith("sqlite"):
        print(f"unsupported DB URI: {uri}")
        return 2

    raw = uri.split("sqlite:///", 1)[1]
    is_windows_abs = len(raw) >= 2 and raw[1] == ":"
    is_unix_abs = raw.startswith("/")
    path = raw if (is_unix_abs or is_windows_abs) else str(
        (Path(__file__).resolve().parent.parent / raw)
    )

    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()

    cur.execute("PRAGMA table_info(chat_conversation_members)")
    existing = {row[1] for row in cur.fetchall()}

    if not existing:
        print("table chat_conversation_members not found — nothing to migrate")
        con.close()
        return 4

    changed = []
    if "is_pinned" not in existing:
        cur.execute(
            "ALTER TABLE chat_conversation_members "
            "ADD COLUMN is_pinned BOOLEAN NOT NULL DEFAULT 0"
        )
        changed.append("col:is_pinned")

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
