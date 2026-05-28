"""
Migration: Create treasury_auto_rules table
"""
import sqlite3
import os
from pathlib import Path

# Match the path from config.py 
DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create treasury_auto_rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treasury_auto_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            match_text TEXT NOT NULL,
            match_type TEXT NOT NULL DEFAULT 'contains',
            action_type TEXT NOT NULL,
            category_code TEXT,
            create_dds INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add auto_rule_id column to treasury_transactions if table exists and column not exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='treasury_transactions'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(treasury_transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        if "auto_rule_id" not in columns:
            cursor.execute("ALTER TABLE treasury_transactions ADD COLUMN auto_rule_id TEXT")
            print("Added auto_rule_id column to treasury_transactions")
    else:
        print("treasury_transactions table does not exist yet, skipping column addition")

    conn.commit()
    conn.close()
    print("Migration completed: treasury_auto_rules table created")

if __name__ == "__main__":
    migrate()
