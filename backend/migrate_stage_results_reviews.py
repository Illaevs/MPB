import sqlite3
from pathlib import Path


def add_column(cur, table, column_def):
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(stage_results)")
    existing = {row[1] for row in cur.fetchall()}

    if "version_number" not in existing:
        add_column(cur, "stage_results", "version_number INTEGER")
    if "status" not in existing:
        add_column(cur, "stage_results", "status TEXT DEFAULT 'review'")
    if "reviewer_comment" not in existing:
        add_column(cur, "stage_results", "reviewer_comment TEXT")
    if "reviewer_id" not in existing:
        add_column(cur, "stage_results", "reviewer_id TEXT")
    if "reviewed_at" not in existing:
        add_column(cur, "stage_results", "reviewed_at TIMESTAMP")
    if "updated_at" not in existing:
        add_column(cur, "stage_results", "updated_at TIMESTAMP")

    conn.commit()
    conn.close()
    print("Stage results review columns ready.")


if __name__ == "__main__":
    main()
