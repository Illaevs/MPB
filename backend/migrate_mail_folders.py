#!/usr/bin/env python3
"""
Idempotent migration for mail folders.
"""
import sqlite3
import os
from pathlib import Path


def _database_uri() -> str:
    try:
        from app.core.config import settings
        return settings.SQLALCHEMY_DATABASE_URI
    except RuntimeError:
        return os.getenv("SQLALCHEMY_DATABASE_URI") or f"sqlite:///{Path(__file__).resolve().parent / 'crm.db'}"


def _sqlite_path() -> str:
    prefix = "sqlite:///"
    uri = _database_uri()
    if not uri.startswith(prefix):
        raise RuntimeError("Only SQLite migration is supported by this script")
    return uri[len(prefix):]


def _columns(cur, table: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def migrate() -> None:
    db_path = _sqlite_path()
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mail_messages'")
        if not cur.fetchone():
            print("mail_messages table not found; skipped")
            return
        cols = _columns(cur, "mail_messages")
        if "folder" not in cols:
            cur.execute("ALTER TABLE mail_messages ADD COLUMN folder VARCHAR(64) NOT NULL DEFAULT 'inbox'")
        if "cc_addr" not in cols:
            cur.execute("ALTER TABLE mail_messages ADD COLUMN cc_addr VARCHAR(1024)")
        cur.execute("UPDATE mail_messages SET folder = 'inbox' WHERE folder IS NULL OR folder = ''")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_mail_messages_mailbox_folder_date "
            "ON mail_messages (mailbox_id, folder, date)"
        )
        conn.commit()
        print("Mail folders migration completed")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
