"""Идемпотентная миграция: корпоративная лента новостей.

Создаёт 4 таблицы:
  feed_posts     — посты
  feed_comments  — комментарии
  feed_reactions — «нравится» (uniq post+user)
  feed_views     — отметки просмотра (uniq post+user)

Запуск:  python backend/migrate_add_feed.py
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
    tables = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    changed: list[str] = []

    if "feed_posts" not in tables:
        cur.execute(
            """
            CREATE TABLE feed_posts (
              id          CHAR(36) PRIMARY KEY,
              author_id   CHAR(36) NOT NULL,
              body        TEXT NOT NULL,
              post_type   VARCHAR(16) NOT NULL DEFAULT 'news',
              is_pinned   BOOLEAN NOT NULL DEFAULT 0,
              attachments JSON NOT NULL DEFAULT '[]',
              created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
              updated_at  DATETIME,
              FOREIGN KEY (author_id) REFERENCES users(id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_posts_created ON feed_posts(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_posts_pinned_created ON feed_posts(is_pinned, created_at)")
        changed.append("feed_posts (+indexes)")

    if "feed_comments" not in tables:
        cur.execute(
            """
            CREATE TABLE feed_comments (
              id         CHAR(36) PRIMARY KEY,
              post_id    CHAR(36) NOT NULL,
              author_id  CHAR(36) NOT NULL,
              body       TEXT NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
              FOREIGN KEY (author_id) REFERENCES users(id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_comments_post_created ON feed_comments(post_id, created_at)")
        changed.append("feed_comments (+index)")

    if "feed_reactions" not in tables:
        cur.execute(
            """
            CREATE TABLE feed_reactions (
              id         CHAR(36) PRIMARY KEY,
              post_id    CHAR(36) NOT NULL,
              user_id    CHAR(36) NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES users(id),
              CONSTRAINT uq_feed_reaction UNIQUE (post_id, user_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_reactions_post ON feed_reactions(post_id)")
        changed.append("feed_reactions (+index)")

    if "feed_views" not in tables:
        cur.execute(
            """
            CREATE TABLE feed_views (
              id         CHAR(36) PRIMARY KEY,
              post_id    CHAR(36) NOT NULL,
              user_id    CHAR(36) NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES users(id),
              CONSTRAINT uq_feed_view UNIQUE (post_id, user_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_views_post ON feed_views(post_id)")
        changed.append("feed_views (+index)")

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
