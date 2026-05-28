#!/usr/bin/env python3
"""
Create daily counters for financial outgoing documents and normalize malformed numbers.
"""
import asyncio
import os
import re
import sys
import uuid
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import inspect, select, text

from app.database.session import async_session, engine
from app.models import OutgoingDocument


FINANCIAL_KINDS = {"invoice", "upd", "vat_invoice"}


def _display_number(value):
    if not value:
        return ""
    return str(value).rsplit(":", 1)[-1]


def _format_number(seq, doc_date):
    return f"{doc_date:%d%m%y}/{int(seq):05d}"


def _seq_from_display(value, doc_date):
    match = re.match(r"^(\d{6})[/\\](\d{5})$", value or "")
    if not match:
        return None
    if match.group(1) != f"{doc_date:%d%m%y}":
        return None
    return int(match.group(2))


async def migrate_schema():
    async with engine.begin() as conn:
        def has_table(sync_conn):
            return inspect(sync_conn).has_table("outgoing_daily_number_sequences")

        exists = await conn.run_sync(has_table)
        if not exists:
            await conn.execute(text("""
                CREATE TABLE outgoing_daily_number_sequences (
                    id VARCHAR(36) PRIMARY KEY,
                    our_company_key VARCHAR(32) NOT NULL,
                    document_kind VARCHAR(32) NOT NULL,
                    sequence_date DATE NOT NULL,
                    next_seq INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_outgoing_daily_number_sequence_scope
            ON outgoing_daily_number_sequences(our_company_key, document_kind, sequence_date)
        """))


async def normalize_numbers():
    async with async_session() as session:
        result = await session.execute(
            select(OutgoingDocument)
            .where(OutgoingDocument.document_kind.in_(FINANCIAL_KINDS))
            .order_by(
                OutgoingDocument.our_company_key,
                OutgoingDocument.document_kind,
                OutgoingDocument.letter_date,
                OutgoingDocument.created_at,
                OutgoingDocument.id,
            )
        )
        groups = defaultdict(list)
        for document in result.scalars().all():
            if not document.letter_date:
                continue
            key = (
                document.our_company_key or "normbud",
                document.document_kind,
                document.letter_date,
            )
            groups[key].append(document)

        for (company_key, document_kind, doc_date), documents in groups.items():
            used = set()
            invalid = []
            for document in documents:
                seq = _seq_from_display(_display_number(document.outgoing_number), doc_date)
                if seq and seq not in used:
                    used.add(seq)
                    document.outgoing_number_company_seq = seq
                    document.outgoing_number = f"{company_key}:{document_kind}:{_format_number(seq, doc_date)}"
                else:
                    invalid.append(document)

            next_seq = 1
            for document in invalid:
                while next_seq in used:
                    next_seq += 1
                used.add(next_seq)
                document.outgoing_number_company_seq = next_seq
                document.outgoing_number = f"{company_key}:{document_kind}:{_format_number(next_seq, doc_date)}"
                next_seq += 1

            max_seq = max(used or {0})
            existing = await session.execute(
                text("""
                    SELECT id FROM outgoing_daily_number_sequences
                    WHERE our_company_key = :company_key
                      AND document_kind = :document_kind
                      AND sequence_date = :sequence_date
                """),
                {
                    "company_key": company_key,
                    "document_kind": document_kind,
                    "sequence_date": doc_date,
                },
            )
            row = existing.first()
            if row:
                await session.execute(
                    text("""
                        UPDATE outgoing_daily_number_sequences
                        SET next_seq = CASE WHEN next_seq > :next_seq THEN next_seq ELSE :next_seq END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """),
                    {"next_seq": max_seq + 1, "id": row[0]},
                )
            else:
                await session.execute(
                    text("""
                        INSERT INTO outgoing_daily_number_sequences
                            (id, our_company_key, document_kind, sequence_date, next_seq, created_at)
                        VALUES
                            (:id, :company_key, :document_kind, :sequence_date, :next_seq, CURRENT_TIMESTAMP)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "company_key": company_key,
                        "document_kind": document_kind,
                        "sequence_date": doc_date,
                        "next_seq": max_seq + 1,
                    },
                )

        await session.commit()


async def main():
    await migrate_schema()
    await normalize_numbers()
    print("Outgoing daily number sequences migrated")


if __name__ == "__main__":
    asyncio.run(main())
