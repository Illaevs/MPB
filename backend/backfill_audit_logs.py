#!/usr/bin/env python3
"""
Backfill audit logs from EventLog and create snapshot entries.
"""
import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import select

from app.database.session import async_session
from app.models import (
    AuditLog,
    EventLog,
    Deal,
    Task,
    Document,
    OutgoingDocument,
    Contract,
    IncomeExpenseEntry,
)
from app.services.audit_log import create_audit_log, serialize_model
from create_audit_log_table import migrate as migrate_audit_table


def _parse_event_details(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


async def _audit_exists(session, source_event_id: str) -> bool:
    result = await session.execute(
        select(AuditLog.id).where(AuditLog.source_event_id == source_event_id)
    )
    return result.scalar_one_or_none() is not None


async def backfill_event_logs(session, limit: Optional[int] = None) -> int:
    result = await session.execute(select(EventLog).order_by(EventLog.created_at.asc()))
    events = result.scalars().all()
    if limit:
        events = events[:limit]
    count = 0
    for event in events:
        source_event_id = str(event.id)
        if await _audit_exists(session, source_event_id):
            continue
        details = _parse_event_details(event.details)
        await create_audit_log(
            session,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action=event.action,
            user_id=event.created_by,
            details=details,
            meta={"source": "event_log"},
            source_event_id=source_event_id,
        )
        count += 1
    return count


async def snapshot_entities(session, limit: Optional[int] = None) -> int:
    entities = [
        ("deal", Deal),
        ("task", Task),
        ("document", Document),
        ("outgoing", OutgoingDocument),
        ("contract", Contract),
        ("income_expense", IncomeExpenseEntry),
    ]
    total = 0
    for entity_type, model in entities:
        result = await session.execute(select(model))
        items = result.scalars().all()
        if limit:
            items = items[:limit]
        for item in items:
            entity_id = getattr(item, "id", None)
            if entity_id is None:
                continue
            source_event_id = f"snapshot:{entity_type}:{entity_id}"
            if await _audit_exists(session, source_event_id):
                continue
            await create_audit_log(
                session,
                entity_type=entity_type,
                entity_id=str(entity_id),
                action="snapshot",
                details={"snapshot": serialize_model(item)},
                meta={"source": "snapshot"},
                source_event_id=source_event_id,
            )
            total += 1
    return total


async def run(args) -> None:
    await migrate_audit_table()
    async with async_session() as session:
        if args.from_event_log:
            count = await backfill_event_logs(session, limit=args.limit)
            print(f"Imported {count} events")
        if args.snapshot:
            count = await snapshot_entities(session, limit=args.limit)
            print(f"Created {count} snapshots")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-event-log", action="store_true", help="Import EventLog into audit_logs")
    parser.add_argument("--snapshot", action="store_true", help="Create snapshot entries")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows per category")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.from_event_log and not args.snapshot:
        args.from_event_log = True
        args.snapshot = True
    asyncio.run(run(args))
