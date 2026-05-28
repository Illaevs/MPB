"""
Bootstrap helpers for user avatars.
"""
from pathlib import Path

from sqlalchemy import inspect, text

from app.core.config import settings
from app.database.session import engine_sync


def _static_root_path() -> Path:
    if settings.STATIC_LOCAL_ROOT:
        return Path(settings.STATIC_LOCAL_ROOT).expanduser()
    return Path(__file__).resolve().parents[2] / "static"


def static_root() -> Path:
    root = _static_root_path()
    root.mkdir(parents=True, exist_ok=True)
    return root


def avatars_root() -> Path:
    root = static_root() / "avatars"
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_user_avatar_schema() -> None:
    static_root()
    avatars_root()

    inspector = inspect(engine_sync)
    if not inspector.has_table("users"):
        return
    try:
        columns = {column["name"] for column in inspector.get_columns("users")}
    except Exception:
        columns = set()
    if "avatar_url" in columns:
        return

    with engine_sync.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
