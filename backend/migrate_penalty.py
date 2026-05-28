"""
Migration script to add penalty system columns to tasks table
and create penalty_rules table
"""
import sqlite3
import os

# Find the database file
db_path = os.path.join(os.path.dirname(__file__), 'crm.db')
if not os.path.exists(db_path):
    db_path = 'crm.db'

print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add new columns to tasks table
columns_to_add = [
    ("final_budget", "REAL"),
    ("rating_coefficient", "REAL"),
    ("deadline_coefficient", "REAL"),
    ("penalty_amount", "REAL"),
]

for col_name, col_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
        print(f"✓ Added column: tasks.{col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"- Column already exists: tasks.{col_name}")
        else:
            print(f"✗ Error adding column {col_name}: {e}")

# Create penalty_rules table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS penalty_rules (
        id VARCHAR(36) PRIMARY KEY,
        rule_type VARCHAR(10) NOT NULL,
        condition_min REAL NOT NULL,
        condition_max REAL NOT NULL,
        coefficient REAL NOT NULL DEFAULT 1.0,
        description VARCHAR(255),
        is_active BOOLEAN DEFAULT 1,
        sort_order REAL DEFAULT 0,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
""")
print("✓ Created table: penalty_rules")

conn.commit()
conn.close()

print("\n✅ Migration completed successfully!")
