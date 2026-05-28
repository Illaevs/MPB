#!/usr/bin/env python3
"""
Create or update messenger tables.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chat_bootstrap import ensure_chat_schema


async def create_tables():
    await ensure_chat_schema()
    print("Messenger tables created or updated successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
