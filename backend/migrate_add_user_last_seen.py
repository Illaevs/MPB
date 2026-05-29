"""Идемпотентная миграция: users.last_seen_at (Phase C.2).

  ALTER TABLE users ADD COLUMN last_seen_at DATETIME

Запуск:
  python backend/migrate_add_user_last_seen.py
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
    cur.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cur.fetchall()}

    if not existing:
        print("table users not found — nothing to migrate")
        con.close()
        return 4

    changed = []
    if "last_seen_at" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN last_seen_at DATETIME")
        changed.append("col:last_seen_at")

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
