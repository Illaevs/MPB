import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM roles")
    roles = {name: role_id for role_id, name in cur.fetchall()}

    targets = []
    for name in ("Суперюзер", "Администратор"):
        role_id = roles.get(name)
        if role_id:
            targets.append(role_id)

    added = 0
    for role_id in targets:
        cur.execute(
            "SELECT 1 FROM role_permissions WHERE role_id = ? AND section = ?",
            (role_id, "tasks_penalties_manage"),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(__import__("uuid").uuid4()), role_id, "tasks_penalties_manage", 1, 0),
        )
        added += 1

    conn.commit()
    conn.close()
    print(f"Penalty permissions added: {added}")


if __name__ == "__main__":
    main()
