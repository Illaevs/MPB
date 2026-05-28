"""
Migration: Add stage_id to income_expense_entries table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import aiosqlite

async def main():
    # Database is in parent directory
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'crm.db')
    print(f"Database path: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(income_expense_entries)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'stage_id' not in column_names:
            print("Adding stage_id column to income_expense_entries table...")
            await db.execute("""
                ALTER TABLE income_expense_entries 
                ADD COLUMN stage_id TEXT
            """)
            await db.commit()
            print("✓ Column added successfully")
        else:
            print("✓ stage_id column already exists")
        
    print("Migration completed!")

if __name__ == '__main__':
    asyncio.run(main())
