"""
Migration: Create task_auctions, task_auction_bids tables and add new columns to tasks and users
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create task_auctions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_auctions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            budget REAL NOT NULL,
            deal_id TEXT REFERENCES deals(id),
            category_code TEXT,
            allow_custom_price INTEGER DEFAULT 0,
            is_block INTEGER DEFAULT 0,
            block_id TEXT REFERENCES task_auctions(id),
            status TEXT DEFAULT 'new',
            winner_id TEXT REFERENCES users(id),
            winner_bid_id TEXT,
            created_task_id TEXT REFERENCES tasks(id),
            created_by_id TEXT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    print("Created task_auctions table")
    
    # Create task_auction_bids table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_auction_bids (
            id TEXT PRIMARY KEY,
            auction_id TEXT NOT NULL REFERENCES task_auctions(id) ON DELETE CASCADE,
            user_id TEXT NOT NULL REFERENCES users(id),
            bid_price REAL NOT NULL,
            comment TEXT,
            covers_children INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    print("Created task_auction_bids table")
    
    # Add rating columns to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN rating REAL DEFAULT 0.0")
        print("Added rating column to users")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("rating column already exists in users")
        else:
            raise
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN rating_count INTEGER DEFAULT 0")
        print("Added rating_count column to users")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("rating_count column already exists in users")
        else:
            raise
    
    # Add new columns to tasks
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN budget REAL")
        print("Added budget column to tasks")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("budget column already exists in tasks")
        else:
            raise
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN category_code TEXT")
        print("Added category_code column to tasks")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("category_code column already exists in tasks")
        else:
            raise
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN source_auction_id TEXT REFERENCES task_auctions(id)")
        print("Added source_auction_id column to tasks")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("source_auction_id column already exists in tasks")
        else:
            raise
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN executor_rating INTEGER")
        print("Added executor_rating column to tasks")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("executor_rating column already exists in tasks")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
