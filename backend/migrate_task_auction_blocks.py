"""
Migration: Add block auctions and bid flags to task_auctions/task_auction_bids
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE task_auctions ADD COLUMN is_block INTEGER DEFAULT 0")
        print("Added is_block column to task_auctions")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("is_block column already exists in task_auctions")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE task_auctions ADD COLUMN block_id TEXT REFERENCES task_auctions(id)")
        print("Added block_id column to task_auctions")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("block_id column already exists in task_auctions")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE task_auction_bids ADD COLUMN covers_children INTEGER DEFAULT 0")
        print("Added covers_children column to task_auction_bids")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("covers_children column already exists in task_auction_bids")
        else:
            raise

    conn.commit()
    conn.close()
    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()
