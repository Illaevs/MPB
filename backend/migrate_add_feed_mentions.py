"""Идемпотентная миграция: обратный индекс упоминаний в ленте.

  feed_mentions — кого упомянули в посте/комментарии (для вкладки
                  «Где меня упомянули» без LIKE %...% по тексту).

Бэкфилл существующих упоминаний выполняется ТОЛЬКО при первом создании
таблицы — поэтому повторный запуск (в т.ч. из migrate_all на старте) не
плодит дубли.

Запуск:  python backend/migrate_add_feed_mentions.py
"""
from __future__ import annotations

import re
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402

# Тот же маркер, что и в роутере ленты: @[Полное Имя](user-uuid).
_MENTION_RE = re.compile(r"@\[[^\]]{1,200}\]\(([0-9a-fA-F][0-9a-fA-F-]{7,})\)")


def _extract_ids(text: str) -> set[str]:
    if not text:
        return set()
    return {m.group(1) for m in _MENTION_RE.finditer(text)}


def _resolve_db_path(uri: str) -> str | None:
    if not uri.startswith("sqlite"):
        print(f"unsupported DB URI: {uri}")
        return None
    raw = uri.split("sqlite:///", 1)[1]
    is_windows_abs = len(raw) >= 2 and raw[1] == ":"
    is_unix_abs = raw.startswith(("/", "\\"))
    return raw if (is_unix_abs or is_windows_abs) else str(
        (Path(__file__).resolve().parent.parent / raw)
    )


def main() -> int:
    path = _resolve_db_path(settings.SQLALCHEMY_DATABASE_URI)
    if path is None:
        return 2
    if not Path(path).exists():
        print(f"db file not found: {path}")
        return 3

    con = sqlite3.connect(path)
    cur = con.cursor()
    tables = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    if "feed_posts" not in tables:
        print("feed_posts not found — run migrate_add_feed.py first")
        con.close()
        return 4

    if "feed_mentions" in tables:
        print("nothing to do — feed_mentions already exists")
        con.close()
        return 0

    cur.execute(
        """
        CREATE TABLE feed_mentions (
          id         CHAR(36) PRIMARY KEY,
          post_id    CHAR(36) NOT NULL,
          comment_id CHAR(36) NULL,
          user_id    CHAR(36) NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_feed_mentions_user_created "
        "ON feed_mentions(user_id, created_at)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_feed_mentions_post ON feed_mentions(post_id)"
    )

    # --- разовый бэкфилл из существующих текстов ---
    valid_users = {r[0] for r in cur.execute("SELECT id FROM users").fetchall()}
    rows: list[tuple] = []

    for post_id, body in cur.execute("SELECT id, body FROM feed_posts").fetchall():
        for uid in _extract_ids(body):
            if uid in valid_users:
                rows.append((str(uuid.uuid4()), post_id, None, uid))

    if "feed_comments" in tables:
        for cid, post_id, body in cur.execute(
            "SELECT id, post_id, body FROM feed_comments"
        ).fetchall():
            for uid in _extract_ids(body):
                if uid in valid_users:
                    rows.append((str(uuid.uuid4()), post_id, cid, uid))

    if rows:
        cur.executemany(
            "INSERT INTO feed_mentions (id, post_id, comment_id, user_id) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )

    con.commit()
    con.close()
    print(f"OK; created feed_mentions, backfilled {len(rows)} mention(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
