#!/usr/bin/env python3
"""
Делает tasks.deal_id NULLABLE — задачи без проекта (в т.ч. «создать
задачу из тикета»).

SQLite не умеет ALTER COLUMN DROP NOT NULL, поэтому таблица
пересобирается по сохранённому в sqlite_master CREATE-SQL (меняем
только NOT NULL у deal_id), данные копируются, индексы воссоздаются.

Idempotent: если deal_id уже nullable — выходим. На не-SQLite
(Postgres) выполняется простой ALTER.
"""
import re

from app.core.config import settings  # noqa: F401  (env-aware -> migrate_all.discover)
from app.database.session import engine_sync

_ = settings.SQLALCHEMY_DATABASE_URI


def _sqlite_rebuild(raw):
    cur = raw.cursor()
    cur.execute("PRAGMA table_info('tasks')")
    info = cur.fetchall()  # cid, name, type, notnull, dflt, pk
    if not info:
        print("tasks table not found — nothing to do")
        return
    deal = [r for r in info if r[1] == "deal_id"]
    if not deal:
        print("tasks.deal_id not found — nothing to do")
        return
    if deal[0][3] == 0:  # notnull flag == 0 -> уже nullable
        print("tasks.deal_id already nullable")
        return

    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    old_sql = cur.fetchone()[0]
    cur.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='tasks' AND sql IS NOT NULL"
    )
    idx_sql = [r[0] for r in cur.fetchall()]

    # Снять NOT NULL только у колонки deal_id.
    new_sql = re.sub(
        r"(?i)(\bdeal_id\b[^,\n]*?)\s+NOT\s+NULL", r"\1", old_sql, count=1
    )
    if new_sql == old_sql:
        raise RuntimeError("Не удалось снять NOT NULL у deal_id (regex miss)")
    # Создаём временную таблицу.
    new_sql = re.sub(
        r'(?is)^\s*CREATE\s+TABLE\s+("tasks"|`tasks`|\[tasks\]|tasks)',
        'CREATE TABLE "tasks__new"',
        new_sql,
        count=1,
    )

    colnames = ", ".join('"%s"' % r[1] for r in info)

    # PRAGMA foreign_keys должен переключаться вне транзакции.
    raw.connection.isolation_level = None
    cur.execute("PRAGMA foreign_keys=OFF")
    cur.execute("BEGIN")
    try:
        cur.execute('DROP TABLE IF EXISTS "tasks__new"')
        cur.execute(new_sql)
        cur.execute(
            f'INSERT INTO "tasks__new" ({colnames}) SELECT {colnames} FROM "tasks"'
        )
        cur.execute('DROP TABLE "tasks"')
        cur.execute('ALTER TABLE "tasks__new" RENAME TO "tasks"')
        for s in idx_sql:
            try:
                cur.execute(s)
            except Exception:  # noqa: BLE001 — индекс мог зависеть от другой схемы
                pass
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        cur.execute("PRAGMA foreign_keys=ON")

    fk = cur.execute("PRAGMA foreign_key_check").fetchall()
    raw.commit()
    print(f"tasks.deal_id -> NULLABLE (rebuilt). foreign_key_check issues: {len(fk)}")


def migrate() -> None:
    dialect = engine_sync.dialect.name
    if dialect == "sqlite":
        raw = engine_sync.raw_connection()
        try:
            _sqlite_rebuild(raw)
        finally:
            raw.close()
        return

    # Postgres / прочие: прямой ALTER (идемпотентно — повтор не вредит).
    from sqlalchemy import text
    with engine_sync.begin() as conn:
        conn.execute(text("ALTER TABLE tasks ALTER COLUMN deal_id DROP NOT NULL"))
    print("tasks.deal_id -> NULLABLE (ALTER)")


if __name__ == "__main__":
    migrate()
