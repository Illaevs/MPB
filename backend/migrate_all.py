#!/usr/bin/env python3
"""
One-shot runner for all idempotent schema migration scripts.

Every `migrate_*.py` / `create_*_column*.py` / `add_*_column*.py` in this
folder is designed to be idempotent (guards with column_exists / swallows
"duplicate column"). Running them all after pulling changes (or on startup
when AUTO_MIGRATE is enabled) keeps an environment from silently drifting
and 500-ing on a missing column.

Heavy / one-off / data-backfill scripts are explicitly excluded.

Usage:
    python migrate_all.py            # run everything (manual catch-up)
    python migrate_all.py --list     # just print what would run

Programmatic:
    from migrate_all import run_all
    summary = run_all()              # {"ok": [...], "failed": [...]}
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Heavy / one-off / destructive / data-backfill — NOT safe to auto-run.
DENYLIST = {
    "migrate_all.py",
    "backfill_audit_logs.py",
    "backfill_outgoing_current_renders.py",
    "create_deal_migration.py",
    "migrate_hotfix_api_500s.py",
    "migrate_users_roles.py",
}

PATTERNS = ("migrate_*.py", "create_*column*.py", "add_*column*.py")


def _is_env_aware(path: str) -> bool:
    """Only scripts that read settings.SQLALCHEMY_DATABASE_URI target the
    configured DB. Legacy one-offs that bare `sqlite3.connect()` a default
    path would hit the wrong DB ("no such table") under a non-default
    env, so they are NOT boot-safe and are skipped."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            src = fh.read()
    except OSError:
        return False
    return ("app.core.config import settings" in src
            or "SQLALCHEMY_DATABASE_URI" in src)


def discover() -> list:
    names = set()
    for pat in PATTERNS:
        for path in glob.glob(os.path.join(HERE, pat)):
            base = os.path.basename(path)
            if base in DENYLIST:
                continue
            if base.startswith("seed_") or base.startswith("test_"):
                continue
            if not _is_env_aware(path):
                continue
            names.add(base)
    return sorted(names)


def run_all(verbose: bool = True) -> dict:
    scripts = discover()
    # Force UTF-8 so scripts that print ✓/✗ don't crash on Windows cp1251
    # when stdout is a captured pipe.
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    ok, failed = [], []
    for name in scripts:
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(HERE, name)],
                cwd=HERE,
                env=child_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if proc.returncode == 0:
                ok.append(name)
                if verbose:
                    print(f"[ok]   {name}")
            else:
                failed.append(name)
                if verbose:
                    tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
                    print(f"[FAIL] {name}: {' | '.join(tail)}")
        except subprocess.TimeoutExpired:
            failed.append(name)
            if verbose:
                print(f"[FAIL] {name}: timeout")
        except Exception as exc:  # noqa: BLE001
            failed.append(name)
            if verbose:
                print(f"[FAIL] {name}: {exc}")
    if verbose:
        print(f"\nMigrations: {len(ok)} ok, {len(failed)} failed"
              + (f" -> {failed}" if failed else ""))
    return {"ok": ok, "failed": failed}


if __name__ == "__main__":
    if "--list" in sys.argv:
        for n in discover():
            print(n)
        sys.exit(0)
    result = run_all()
    sys.exit(1 if result["failed"] else 0)
