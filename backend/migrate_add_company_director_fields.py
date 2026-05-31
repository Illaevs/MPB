"""Идемпотентная миграция: структурный ЕИО в companies.

  ALTER TABLE companies ADD COLUMN director_last_name VARCHAR(120)
  ALTER TABLE companies ADD COLUMN director_first_name VARCHAR(120)
  ALTER TABLE companies ADD COLUMN director_middle_name VARCHAR(120)
  ALTER TABLE companies ADD COLUMN director_position VARCHAR(160)

Запуск:
  python backend/migrate_add_company_director_fields.py
Env-aware (читает settings.SQLALCHEMY_DATABASE_URI) → подхватывается
AUTO_MIGRATE через migrate_all.discover().
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402


COLUMNS = {
    "director_last_name": "VARCHAR(120)",
    "director_first_name": "VARCHAR(120)",
    "director_middle_name": "VARCHAR(120)",
    "director_position": "VARCHAR(160)",
}


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
    cur.execute("PRAGMA table_info(companies)")
    existing = {row[1] for row in cur.fetchall()}

    if not existing:
        print("table companies not found — nothing to migrate")
        con.close()
        return 4

    changed = []
    for col, ddl_type in COLUMNS.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE companies ADD COLUMN {col} {ddl_type}")
            changed.append(f"col:{col}")

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
