"""
Add our_company_id field to deals table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiosqlite

async def main():
    # Database is in parent directory (same as app/core/config.py: "../crm.db")
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'crm.db')
    print(f"Database path: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(deals)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'our_company_id' not in column_names:
            print("Adding our_company_id column to deals table...")
            await db.execute("""
                ALTER TABLE deals 
                ADD COLUMN our_company_id TEXT
            """)
            await db.commit()
            print("✓ Column added successfully")
        else:
            print("✓ Column our_company_id already exists")
        
        print("Migration completed!")

if __name__ == '__main__':
    asyncio.run(main())
