import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS penalty_rules (
            id TEXT PRIMARY KEY,
            rule_type TEXT NOT NULL,
            condition_min REAL NOT NULL,
            condition_max REAL NOT NULL,
            coefficient REAL NOT NULL DEFAULT 1.0,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()
    print("Penalty rules table ready.")


if __name__ == "__main__":
    main()
