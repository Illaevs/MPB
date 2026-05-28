"""Идемпотентная миграция: лента — фаза 2.

  feed_posts.poll        — JSON-конфиг опроса (nullable)
  feed_poll_votes        — голоса в опросах
  feed_reactions.emoji   — эмодзи реакции; уникальность меняется с
                           (post_id,user_id) на (post_id,user_id,emoji),
                           поэтому таблица пересоздаётся (старые лайки → 👍).

Запуск:  python backend/migrate_add_feed_phase2.py
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

    tables = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    # feed_posts отсутствует — фаза 1 не накатывалась.
    if "feed_posts" not in tables:
        print("feed_posts not found — run migrate_add_feed.py first")
        con.close()
        return 4

    # 1) feed_posts.poll
    post_cols = {r[1] for r in cur.execute("PRAGMA table_info('feed_posts')").fetchall()}
    if "poll" not in post_cols:
        cur.execute("ALTER TABLE feed_posts ADD COLUMN poll JSON NULL")
        changed.append("feed_posts.poll")

    # 2) feed_poll_votes
    if "feed_poll_votes" not in tables:
        cur.execute(
            """
            CREATE TABLE feed_poll_votes (
              id         CHAR(36) PRIMARY KEY,
              post_id    CHAR(36) NOT NULL,
              option_id  CHAR(36) NOT NULL,
              user_id    CHAR(36) NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES users(id),
              CONSTRAINT uq_feed_poll_vote UNIQUE (post_id, user_id, option_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_poll_votes_post ON feed_poll_votes(post_id)")
        changed.append("feed_poll_votes (+index)")

    # 3) feed_reactions.emoji — нужна смена уникального ключа, поэтому
    #    таблицу пересоздаём (данных в свежей ленте мало; старые лайки → 👍).
    reaction_cols = {r[1] for r in cur.execute("PRAGMA table_info('feed_reactions')").fetchall()}
    if "emoji" not in reaction_cols:
        cur.execute("ALTER TABLE feed_reactions RENAME TO feed_reactions_old")
        cur.execute(
            """
            CREATE TABLE feed_reactions (
              id         CHAR(36) PRIMARY KEY,
              post_id    CHAR(36) NOT NULL,
              user_id    CHAR(36) NOT NULL,
              emoji      VARCHAR(16) NOT NULL DEFAULT '👍',
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (post_id) REFERENCES feed_posts(id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES users(id),
              CONSTRAINT uq_feed_reaction UNIQUE (post_id, user_id, emoji)
            )
            """
        )
        cur.execute(
            "INSERT INTO feed_reactions (id, post_id, user_id, emoji, created_at) "
            "SELECT id, post_id, user_id, '👍', created_at FROM feed_reactions_old"
        )
        cur.execute("DROP TABLE feed_reactions_old")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_feed_reactions_post ON feed_reactions(post_id)")
        changed.append("feed_reactions.emoji (table rebuilt)")

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
