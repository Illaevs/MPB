import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM roles")
    roles = {name: role_id for role_id, name in cur.fetchall()}

    targets_all = [roles.get("Суперюзер"), roles.get("Администратор")]
    targets_assigned = [roles.get("ГИП")]

    added = 0
    for role_id in [r for r in targets_all if r]:
        cur.execute(
            "SELECT 1 FROM role_permissions WHERE role_id = ? AND section = ?",
            (role_id, "work_results_reviews"),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(__import__("uuid").uuid4()), role_id, "work_results_reviews", 1, 0),
        )
        added += 1

    for role_id in [r for r in targets_assigned if r]:
        cur.execute(
            "SELECT 1 FROM role_permissions WHERE role_id = ? AND section = ?",
            (role_id, "work_results_reviews"),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(__import__("uuid").uuid4()), role_id, "work_results_reviews", 0, 1),
        )
        added += 1

    conn.commit()
    conn.close()
    print(f"Work results review permissions added: {added}")


if __name__ == "__main__":
    main()
