"""Идемпотентная миграция: аудит загрузок документов договора (кто/когда), пофайлово.

  ALTER TABLE contract_documents ADD COLUMN pdf_uploaded_by  VARCHAR(255)
  ALTER TABLE contract_documents ADD COLUMN pdf_uploaded_at  DATETIME
  ALTER TABLE contract_documents ADD COLUMN edit_uploaded_by VARCHAR(255)
  ALTER TABLE contract_documents ADD COLUMN edit_uploaded_at DATETIME

Затем best-effort BACKFILL отображаемого имени автора и времени загрузки из:
  1) event_logs  (action LIKE 'contract.document.upload%', details.document_id,
     created_by -> users.full_name/email)
  2) audit_logs  (если таблица существует; та же логика по details.document_id /
     entity_id, user_id -> users.full_name/email)
  3) upload_jobs (module='contracts', meta.document_id, meta.uploaded_by или
     created_by -> users.full_name/email)

Где автора/время восстановить нельзя — оставляем NULL. Бэкфилл не падает на
отсутствии записей/таблиц.

Запуск:
  python backend/migrate_contract_document_upload_audit.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402


def _table_exists(cur, name: str) -> bool:
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def _columns(cur, table: str) -> set:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _load_user_names(cur) -> dict:
    """user_id (str, with and without dashes) -> display name."""
    names: dict = {}
    if not _table_exists(cur, "users"):
        return names
    cols = _columns(cur, "users")
    name_col = "full_name" if "full_name" in cols else ("email" if "email" in cols else None)
    if not name_col:
        return names
    cur.execute(f"SELECT id, {name_col} FROM users")
    for uid, display in cur.fetchall():
        if uid is None:
            continue
        value = display or (None)
        if not value and "email" in cols and name_col != "email":
            # fall back to email if full_name is empty
            value = None
        if not value:
            continue
        key = str(uid)
        names[key] = value
        names[key.replace("-", "")] = value
    return names


def _resolve_name(user_names: dict, user_id) -> str | None:
    if not user_id:
        return None
    key = str(user_id)
    return user_names.get(key) or user_names.get(key.replace("-", ""))


def _norm_id(value) -> str:
    return str(value or "").replace("-", "")


def _backfill_from_log(cur, table: str, user_names: dict, target: dict) -> int:
    """Collect (document_id_norm -> {by, at}) from a log table.

    target is mutated; earlier (older) records win for a given doc so that the
    FIRST upload is reflected. We process rows ordered by created_at ASC and
    only set if not already present.
    Returns number of (doc, kind) attributions recorded.
    """
    if not _table_exists(cur, table):
        return 0
    cols = _columns(cur, table)
    user_col = "created_by" if "created_by" in cols else ("user_id" if "user_id" in cols else None)
    has_details = "details" in cols
    has_created = "created_at" in cols
    order = " ORDER BY created_at ASC" if has_created else ""
    select_cols = ["action"]
    if user_col:
        select_cols.append(user_col)
    if has_details:
        select_cols.append("details")
    if has_created:
        select_cols.append("created_at")
    select_cols.append("entity_id" if "entity_id" in cols else "NULL AS entity_id")
    try:
        cur.execute(
            f"SELECT {', '.join(select_cols)} FROM {table} "
            f"WHERE action LIKE 'contract.document.upload%'{order}"
        )
        rows = cur.fetchall()
    except sqlite3.Error:
        return 0

    count = 0
    for row in rows:
        data = dict(zip([c.split(" AS ")[-1] for c in select_cols], row))
        details_raw = data.get("details")
        document_id = None
        file_kind = None
        if details_raw:
            try:
                parsed = json.loads(details_raw)
                document_id = parsed.get("document_id")
                file_kind = parsed.get("file_kind")
            except (ValueError, TypeError):
                document_id = None
        if not document_id:
            continue
        doc_key = _norm_id(document_id)
        user_id = data.get(user_col) if user_col else None
        name = _resolve_name(user_names, user_id)
        at = data.get("created_at")
        if not name and not at:
            continue
        kinds = [file_kind] if file_kind in ("pdf", "edit") else ["pdf", "edit"]
        for kind in kinds:
            slot = target.setdefault((doc_key, kind), {"by": None, "at": None})
            if slot["by"] is None and name:
                slot["by"] = name
                count += 1
            if slot["at"] is None and at:
                slot["at"] = at


    return count


def _backfill_from_upload_jobs(cur, user_names: dict, target: dict) -> int:
    if not _table_exists(cur, "upload_jobs"):
        return 0
    cols = _columns(cur, "upload_jobs")
    has_meta = "meta" in cols
    has_created = "created_at" in cols
    order = " ORDER BY created_at ASC" if has_created else ""
    sel = ["file_kind", "created_by"]
    if has_meta:
        sel.append("meta")
    if has_created:
        sel.append("created_at")
    try:
        cur.execute(
            f"SELECT {', '.join(sel)} FROM upload_jobs WHERE module='contracts'{order}"
        )
        rows = cur.fetchall()
    except sqlite3.Error:
        return 0

    count = 0
    for row in rows:
        data = dict(zip(sel, row))
        meta_raw = data.get("meta")
        document_id = None
        meta_kind = None
        meta_uploaded_by = None
        if meta_raw:
            try:
                meta = meta_raw if isinstance(meta_raw, dict) else json.loads(meta_raw)
                document_id = meta.get("document_id")
                meta_kind = meta.get("file_kind")
                meta_uploaded_by = meta.get("uploaded_by")
            except (ValueError, TypeError):
                document_id = None
        if not document_id:
            continue
        doc_key = _norm_id(document_id)
        kind = meta_kind or data.get("file_kind")
        name = meta_uploaded_by or _resolve_name(user_names, data.get("created_by"))
        at = data.get("created_at")
        if not name and not at:
            continue
        kinds = [kind] if kind in ("pdf", "edit") else ["pdf", "edit"]
        for k in kinds:
            slot = target.setdefault((doc_key, k), {"by": None, "at": None})
            if slot["by"] is None and name:
                slot["by"] = name
                count += 1
            if slot["at"] is None and at:
                slot["at"] = at
    return count


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

    if not _table_exists(cur, "contract_documents"):
        print("table contract_documents not found — nothing to migrate")
        con.close()
        return 4

    existing = _columns(cur, "contract_documents")

    new_cols = [
        ("pdf_uploaded_by", "VARCHAR(255)"),
        ("pdf_uploaded_at", "DATETIME"),
        ("edit_uploaded_by", "VARCHAR(255)"),
        ("edit_uploaded_at", "DATETIME"),
    ]
    changed = []
    for col, sql_type in new_cols:
        if col not in existing:
            cur.execute(f"ALTER TABLE contract_documents ADD COLUMN {col} {sql_type}")
            changed.append(f"col:{col}")
    con.commit()

    # ---- BACKFILL (best-effort) ----
    backfilled = 0
    try:
        user_names = _load_user_names(cur)
        # (document_id_norm, kind) -> {"by": name, "at": ts}
        target: dict = {}
        _backfill_from_log(cur, "event_logs", user_names, target)
        _backfill_from_log(cur, "audit_logs", user_names, target)
        _backfill_from_upload_jobs(cur, user_names, target)

        if target:
            # Map normalized doc ids -> actual contract_documents rows that
            # currently have a file of that kind but no audit author/time yet.
            cur.execute(
                "SELECT id, pdf_storage_path, edit_storage_path, "
                "pdf_uploaded_by, pdf_uploaded_at, edit_uploaded_by, edit_uploaded_at "
                "FROM contract_documents"
            )
            doc_rows = cur.fetchall()
            for (
                doc_id,
                pdf_path,
                edit_path,
                pdf_by,
                pdf_at,
                edit_by,
                edit_at,
            ) in doc_rows:
                doc_key = _norm_id(doc_id)
                for kind, has_file, cur_by, cur_at in (
                    ("pdf", pdf_path, pdf_by, pdf_at),
                    ("edit", edit_path, edit_by, edit_at),
                ):
                    slot = target.get((doc_key, kind))
                    if not slot or not has_file:
                        continue
                    set_parts = []
                    params = []
                    if cur_by is None and slot.get("by"):
                        set_parts.append(f"{kind}_uploaded_by = ?")
                        params.append(slot["by"])
                    if cur_at is None and slot.get("at"):
                        set_parts.append(f"{kind}_uploaded_at = ?")
                        params.append(slot["at"])
                    if set_parts:
                        params.append(doc_id)
                        cur.execute(
                            f"UPDATE contract_documents SET {', '.join(set_parts)} WHERE id = ?",
                            params,
                        )
                        backfilled += 1
            con.commit()
    except Exception as exc:  # noqa: BLE001 - backfill is best-effort
        print(f"backfill skipped due to error: {exc}")

    con.close()

    summary = []
    if changed:
        summary.append(f"applied: {', '.join(changed)}")
    else:
        summary.append("columns already present")
    summary.append(f"backfilled file-attributions: {backfilled}")
    print("OK; " + "; ".join(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
