"""Идемпотентная миграция: расширенные профили + отсутствия.

Создаёт две таблицы:
  user_profiles  — карточка сотрудника (1-к-1 с users)
  user_absences  — записи об отпуске/больничном/командировке

Запуск:
  python backend/migrate_add_profiles_absences.py
DB-путь берётся из SQLALCHEMY_DATABASE_URI (см. env / .env / config.py).
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
        print(f"unsupported DB URI for this migration: {uri}")
        return 2
    # sqlite:////abs/path (unix, 4 слеша) → rest='/abs/path';
    # sqlite:///C:/path (windows) → rest='C:/path';
    # sqlite:///rel/path → относительный (от родителя backend/).
    rest = uri.split("sqlite:///", 1)[1]
    if rest.startswith(("/", "\\")) or (len(rest) >= 2 and rest[1] == ":"):
        path = rest
    else:
        path = str((Path(__file__).resolve().parent.parent / rest))
    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()
    changed: list[str] = []

    tables = {row[0] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    # 1) user_profiles
    if "user_profiles" not in tables:
        cur.execute(
            """
            CREATE TABLE user_profiles (
              id                CHAR(36) PRIMARY KEY,
              user_id           CHAR(36) NOT NULL UNIQUE,
              job_title         VARCHAR(255) NULL,
              department        VARCHAR(255) NULL,
              manager_id        CHAR(36) NULL,
              hire_date         DATE NULL,
              birth_date        DATE NULL,
              birth_show_year   BOOLEAN NOT NULL DEFAULT 1,
              bio               TEXT NULL,
              interests         JSON NOT NULL DEFAULT '[]',
              skills            JSON NOT NULL DEFAULT '[]',
              telegram_username VARCHAR(64) NULL,
              created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
              updated_at        DATETIME,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
              FOREIGN KEY (manager_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_user_profiles_user "
            "ON user_profiles(user_id)"
        )
        changed.append("user_profiles (+index)")

    # 2) user_absences
    if "user_absences" not in tables:
        cur.execute(
            """
            CREATE TABLE user_absences (
              id           CHAR(36) PRIMARY KEY,
              user_id      CHAR(36) NOT NULL,
              type         VARCHAR(20) NOT NULL,
              date_from    DATE NOT NULL,
              date_to      DATE NOT NULL,
              comment      TEXT NULL,
              created_by   CHAR(36) NULL,
              created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
              updated_at   DATETIME,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
              FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_user_absences_dates "
            "ON user_absences(date_from, date_to)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_user_absences_user_dates "
            "ON user_absences(user_id, date_from)"
        )
        changed.append("user_absences (+indexes)")

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
