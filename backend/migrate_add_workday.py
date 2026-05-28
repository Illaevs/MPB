"""Идемпотентная миграция: добавить роли поля учёта времени + создать
таблицу work_sessions.

Запуск:
  python backend/migrate_add_workday.py
DB-путь берётся из SQLALCHEMY_DATABASE_URI (см. env / .env / config.py).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

# Make `from app...` imports work when run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402


def main() -> int:
    uri = settings.SQLALCHEMY_DATABASE_URI
    if not uri.startswith("sqlite"):
        print(f"unsupported DB URI for this migration: {uri}")
        return 2
    # sqlite:///abs/path.db  or  sqlite:////abs/path.db
    path = uri.split("sqlite:///", 1)[1]
    path = path.lstrip("/")
    if not path.startswith(("/", "\\")) and len(path) >= 2 and path[1] != ":":
        # relative path → resolve against parent of backend/
        path = str((Path(__file__).resolve().parent.parent / path))
    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()
    changed: list[str] = []

    # 1) roles.track_work_time / idle_timeout_minutes
    cols = {row[1] for row in cur.execute("PRAGMA table_info('roles')").fetchall()}
    if "track_work_time" not in cols:
        cur.execute(
            "ALTER TABLE roles ADD COLUMN track_work_time BOOLEAN NOT NULL DEFAULT 0"
        )
        changed.append("roles.track_work_time")
    if "idle_timeout_minutes" not in cols:
        cur.execute(
            "ALTER TABLE roles ADD COLUMN idle_timeout_minutes INTEGER NULL"
        )
        changed.append("roles.idle_timeout_minutes")

    # 2) work_sessions
    tables = {row[0] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "work_sessions" not in tables:
        cur.execute(
            """
            CREATE TABLE work_sessions (
              id               CHAR(36) PRIMARY KEY,
              user_id          CHAR(36) NOT NULL,
              started_at       DATETIME NOT NULL,
              ended_at         DATETIME NULL,
              ended_reason     VARCHAR(16) NULL,
              last_activity_at DATETIME NOT NULL,
              note_start       TEXT NULL,
              note_end         TEXT NULL,
              created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
              updated_at       DATETIME,
              FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_work_sessions_user_started "
            "ON work_sessions(user_id, started_at)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_work_sessions_user_active "
            "ON work_sessions(user_id, ended_at)"
        )
        changed.append("work_sessions (+indexes)")

    con.commit()
    con.close()

    if changed:
        print("migration applied:")
        for c in changed:
            print(f"  + {c}")
    else:
        print("nothing to do — schema already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
