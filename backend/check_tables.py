"""
Check database tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import aiosqlite

async def main():
    db_path = os.path.join(os.path.dirname(__file__), 'crm.db')
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = await cursor.fetchall()
        
        print("=== Database Tables ===")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if 'deal' or 'deals' exists
        table_names = [t[0] for t in tables]
        if 'deal' in table_names:
            print("\n✓ Found table: deal")
            cursor = await db.execute("PRAGMA table_info(deal)")
            columns = await cursor.fetchall()
            print("\nColumns in 'deal' table:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        elif 'deals' in table_names:
            print("\n✓ Found table: deals")
            cursor = await db.execute("PRAGMA table_info(deals)")
            columns = await cursor.fetchall()
            print("\nColumns in 'deals' table:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

if __name__ == '__main__':
    asyncio.run(main())
