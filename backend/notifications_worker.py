#!/usr/bin/env python3
"""
Background worker for notification rules engine.
"""
import asyncio

from app.database.session import async_session
from app.services.notifications_engine import (
    process_event_logs,
    process_task_overdue,
    process_document_overdue,
    process_digests,
    process_data_health_daily_summary,
)
from app.services.notification_delivery import process_telegram_deliveries
from app.services.telegram_bot import fetch_telegram_updates, set_telegram_bot_commands, telegram_bot_configured
from app.services.telegram_commands import BOT_COMMANDS
from app.services.telegram_updates import handle_telegram_update


async def run_loop():
    telegram_update_offset = None
    telegram_updates_initialized = False
    telegram_commands_initialized = False
    maintenance_tick = 0

    while True:
        async with async_session() as db:
            if maintenance_tick % 4 == 0:
                await process_event_logs(db)
                await process_task_overdue(db)
                await process_document_overdue(db)
                await process_digests(db)
                await process_data_health_daily_summary(db)
                await process_telegram_deliveries(db)
            if telegram_bot_configured():
                try:
                    if not telegram_commands_initialized:
                        await set_telegram_bot_commands(BOT_COMMANDS)
                        telegram_commands_initialized = True
                    updates = await fetch_telegram_updates(offset=telegram_update_offset)
                    if updates:
                        telegram_update_offset = int(updates[-1]["update_id"]) + 1
                        if telegram_updates_initialized:
                            for update in updates:
                                await handle_telegram_update(db, update)
                    telegram_updates_initialized = True
                except Exception:
                    telegram_updates_initialized = True
        maintenance_tick += 1
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(run_loop())
