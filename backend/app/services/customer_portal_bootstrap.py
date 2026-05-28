"""
Bootstrap helpers for customer portal role/permissions.
"""
from __future__ import annotations

import uuid

from sqlalchemy import text

from app.database.session import engine_sync


CUSTOMER_ROLE_NAME = "Заказчик"
CUSTOMER_ROLE_DESCRIPTION = "Роль для доступа к кабинету заказчика"
CUSTOMER_SECTION_KEY = "customer_portal"


def ensure_customer_portal_role() -> None:
    with engine_sync.begin() as connection:
        role_row = connection.execute(
            text("SELECT id FROM roles WHERE name = :name LIMIT 1"),
            {"name": CUSTOMER_ROLE_NAME},
        ).fetchone()

        role_id = None
        if role_row:
            role_id = str(role_row[0])
            connection.execute(
                text(
                    """
                    UPDATE roles
                    SET description = COALESCE(description, :description)
                    WHERE id = :role_id
                    """
                ),
                {"role_id": role_id, "description": CUSTOMER_ROLE_DESCRIPTION},
            )
        else:
            role_id = str(uuid.uuid4())
            connection.execute(
                text(
                    """
                    INSERT INTO roles (id, name, description, is_system)
                    VALUES (:id, :name, :description, 0)
                    """
                ),
                {
                    "id": role_id,
                    "name": CUSTOMER_ROLE_NAME,
                    "description": CUSTOMER_ROLE_DESCRIPTION,
                },
            )

        permission_row = connection.execute(
            text(
                """
                SELECT id
                FROM role_permissions
                WHERE role_id = :role_id AND section = :section
                LIMIT 1
                """
            ),
            {"role_id": role_id, "section": CUSTOMER_SECTION_KEY},
        ).fetchone()

        if permission_row:
            connection.execute(
                text(
                    """
                    UPDATE role_permissions
                    SET read_all = 0,
                        read_assigned = 1
                    WHERE id = :permission_id
                    """
                ),
                {"permission_id": str(permission_row[0])},
            )
        else:
            connection.execute(
                text(
                    """
                    INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
                    VALUES (:id, :role_id, :section, 0, 1)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "role_id": role_id,
                    "section": CUSTOMER_SECTION_KEY,
                },
            )

        system_roles = connection.execute(
            text("SELECT id FROM roles WHERE is_system = 1")
        ).fetchall()

        for system_role in system_roles:
            system_role_id = str(system_role[0])
            system_permission_row = connection.execute(
                text(
                    """
                    SELECT id
                    FROM role_permissions
                    WHERE role_id = :role_id AND section = :section
                    LIMIT 1
                    """
                ),
                {"role_id": system_role_id, "section": CUSTOMER_SECTION_KEY},
            ).fetchone()

            if system_permission_row:
                connection.execute(
                    text(
                        """
                        UPDATE role_permissions
                        SET read_all = 1,
                            read_assigned = 1
                        WHERE id = :permission_id
                        """
                    ),
                    {"permission_id": str(system_permission_row[0])},
                )
            else:
                connection.execute(
                    text(
                        """
                        INSERT INTO role_permissions (id, role_id, section, read_all, read_assigned)
                        VALUES (:id, :role_id, :section, 1, 1)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "role_id": system_role_id,
                        "section": CUSTOMER_SECTION_KEY,
                    },
                )
