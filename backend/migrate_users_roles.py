#!/usr/bin/env python3
"""
Migration script to add users/roles/permissions and related links.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


async def migrate_users_roles():
    async with async_session() as session:
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_system INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id TEXT PRIMARY KEY,
                    role_id TEXT NOT NULL,
                    section TEXT NOT NULL,
                    read_all INTEGER DEFAULT 0,
                    read_assigned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS company_user_links (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    link_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS deal_gips (
                    id TEXT PRIMARY KEY,
                    deal_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role
                ON users(role_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_role_permissions_role
                ON role_permissions(role_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_company_user_links_company
                ON company_user_links(company_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_company_user_links_user
                ON company_user_links(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deal_gips_deal
                ON deal_gips(deal_id)
            """))
            await session.commit()
            print("Users/Roles tables migrated")
        except Exception as exc:
            await session.rollback()
            print(f"Migration failed: {exc}")
            raise

    async with async_session() as session:
        try:
            await session.execute(text("""
                ALTER TABLE tasks ADD COLUMN assigned_to_user_id TEXT
            """))
            await session.execute(text("""
                ALTER TABLE tasks ADD COLUMN created_by_user_id TEXT
            """))
            await session.commit()
            print("Tasks columns migrated")
        except Exception as exc:
            await session.rollback()
            if "duplicate column name" in str(exc).lower():
                print("Task user columns already exist")
                return
            print(f"Task migration failed: {exc}")
            raise


async def main():
    await migrate_users_roles()


if __name__ == "__main__":
    asyncio.run(main())
