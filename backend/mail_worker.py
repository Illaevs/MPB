#!/usr/bin/env python3
"""
Background worker for IMAP polling.
"""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.database.session import async_session
from app.models import Mailbox
from app.services.mail_sync import sync_mailbox


async def run_loop():
    interval = max(int(settings.MAIL_POLL_INTERVAL_SECONDS or 60), 10)
    while True:
        async with async_session() as db:
            result = await db.execute(
                select(Mailbox).where(Mailbox.status == "connected")
            )
            mailboxes = result.scalars().all()
            for mailbox in mailboxes:
                try:
                    await sync_mailbox(db, mailbox, limit=50)
                except Exception:
                    # Keep worker running even if one mailbox fails
                    continue
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(run_loop())
