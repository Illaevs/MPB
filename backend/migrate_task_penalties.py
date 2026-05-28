import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(tasks)")
    existing = {row[1] for row in cur.fetchall()}

    columns = [
        ("final_budget", "FLOAT"),
        ("rating_coefficient", "FLOAT"),
        ("deadline_coefficient", "FLOAT"),
        ("penalty_amount", "FLOAT"),
    ]

    added = 0
    for name, ctype in columns:
        if name in existing:
            continue
        cur.execute(f"ALTER TABLE tasks ADD COLUMN {name} {ctype}")
        added += 1

    conn.commit()
    conn.close()
    print(f"Migration complete. Added {added} column(s).")


if __name__ == "__main__":
    main()
