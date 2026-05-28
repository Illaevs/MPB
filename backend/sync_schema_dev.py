"""DEV-ONLY: досинхронизировать схему локальной SQLite-БД с моделями.

Локальная `crm.db` сильно отстаёт: часть таблиц/колонок добавлялись
миграциями, которые на дев-копию не накатывали. Этот скрипт:
  1) создаёт отсутствующие таблицы (Base.metadata.create_all);
  2) для каждой существующей таблицы добавляет недостающие колонки
     через ALTER TABLE ADD COLUMN.

Ограничения SQLite ALTER ADD COLUMN: нельзя добавить NOT NULL без
DEFAULT и нельзя добавить UNIQUE. Поэтому такие колонки добавляем
как nullable / с дефолтом — для дев-БД это приемлемо.

НЕ для продакшна — там полноценные миграции.

Запуск:  python backend/sync_schema_dev.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402,F401 — регистрирует все модели


def _sqlite_type(col) -> str:
    """Грубое отображение типа SQLAlchemy → SQLite affinity."""
    try:
        from sqlalchemy.dialects import sqlite as _sqlite
        return col.type.compile(dialect=_sqlite.dialect())
    except Exception:
        return "TEXT"


def main() -> int:
    uri = settings.SQLALCHEMY_DATABASE_URI
    if not uri.startswith("sqlite"):
        print(f"unsupported DB URI: {uri}")
        return 2
    path = uri.split("sqlite:///", 1)[1].lstrip("/")
    if not path.startswith(("/", "\\")) and len(path) >= 2 and path[1] != ":":
        path = str((Path(__file__).resolve().parent.parent / path))
    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()

    existing_tables = {
        r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    added_cols: list[str] = []
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            # create_all ниже создаст таблицу целиком — пропускаем.
            continue
        have = {
            r[1] for r in cur.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()
        }
        for col in table.columns:
            if col.name in have:
                continue
            coltype = _sqlite_type(col)
            ddl = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {coltype}'
            # DEFAULT — если у колонки есть скалярный server_default/default.
            default_sql = None
            sd = getattr(col, "server_default", None)
            if sd is not None and getattr(sd, "arg", None) is not None:
                try:
                    default_sql = str(sd.arg.text) if hasattr(sd.arg, "text") else str(sd.arg)
                except Exception:
                    default_sql = None
            if default_sql is None and not col.nullable:
                # NOT NULL без дефолта в SQLite ALTER невозможно — даём дефолт.
                default_sql = "0" if coltype.upper().startswith(("INT", "BOOL", "FLOAT", "REAL", "NUM")) else "''"
            if default_sql is not None:
                ddl += f" DEFAULT {default_sql}"
            try:
                cur.execute(ddl)
                added_cols.append(f"{table_name}.{col.name}")
            except sqlite3.OperationalError as e:
                print(f"  ! skip {table_name}.{col.name}: {e}")

    con.commit()
    con.close()

    # Отсутствующие таблицы — через create_all (синхронно).
    from sqlalchemy import create_engine
    sync_uri = uri.replace("+aiosqlite", "")
    engine = create_engine(sync_uri)
    Base.metadata.create_all(engine)
    engine.dispose()

    if added_cols:
        print(f"added {len(added_cols)} column(s):")
        for c in added_cols:
            print(f"  + {c}")
    else:
        print("no missing columns")
    print("tables ensured via create_all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
