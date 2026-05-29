"""Идемпотентная миграция: chat_message_reactions (Phase B.3).

  CREATE TABLE chat_message_reactions (
    id VARCHAR(36) PK,
    message_id VARCHAR(36) NOT NULL FK -> global_chat_messages.id,
    user_id    VARCHAR(36) NOT NULL FK -> users.id,
    emoji      VARCHAR(32) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (message_id, user_id, emoji)
  )
  CREATE INDEX ix_chat_message_reactions_message ON ... (message_id)

Запуск:
  python backend/migrate_add_chat_message_reactions.py
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
    changed: list[str] = []

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_message_reactions'"
    )
    if cur.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE chat_message_reactions (
                id VARCHAR(36) PRIMARY KEY,
                message_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                emoji VARCHAR(32) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_chat_message_reactions_unique
                    UNIQUE (message_id, user_id, emoji),
                FOREIGN KEY (message_id) REFERENCES global_chat_messages (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        changed.append("table:chat_message_reactions")

    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_message_reactions_message "
        "ON chat_message_reactions (message_id)"
    )

    con.commit()
    con.close()

    if changed:
        print(f"OK; applied: {', '.join(changed)}")
    else:
        print("OK; nothing to do (already migrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
