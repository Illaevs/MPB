import argparse
import asyncio
import re
from typing import Optional, Tuple

from sqlalchemy import select

from app.database.session import async_session
from app.models import OutgoingDocument, Document


def _display_number(value: str) -> str:
    if ":" in value:
        return value.split(":", 1)[1]
    return value


def _parse_prefix(value: str) -> Optional[int]:
    match = re.match(r"^(\d+)", value.strip())
    if not match:
        return None
    return int(match.group(1))


def _map_company(number: int) -> Optional[str]:
    if number < 1000:
        return "morozov"
    if 1000 <= number < 2000:
        return "normbud"
    if number >= 4000:
        return "bayer"
    return None


async def main(dry_run: bool = False) -> None:
    updated = 0
    skipped = 0
    unresolved = 0

    async with async_session() as db:
        result = await db.execute(select(OutgoingDocument))
        documents = result.scalars().all()
        for doc in documents:
            display = _display_number(doc.outgoing_number or "")
            prefix = _parse_prefix(display or "")
            if prefix is None:
                unresolved += 1
                continue
            new_key = _map_company(prefix)
            if not new_key:
                unresolved += 1
                continue
            if doc.our_company_key == new_key:
                skipped += 1
                continue
            new_outgoing_number = f"{new_key}:{display}"
            existing = await db.execute(
                select(OutgoingDocument).where(OutgoingDocument.outgoing_number == new_outgoing_number)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            if dry_run:
                updated += 1
                continue
            doc.our_company_key = new_key
            doc.outgoing_number = new_outgoing_number

            doc_row = await db.execute(
                select(Document).where(
                    Document.source_type == "outgoing_registry",
                    Document.source_id == str(doc.id),
                )
            )
            document_registry = doc_row.scalar_one_or_none()
            if document_registry:
                document_registry.our_company_id = new_key

            await db.commit()
            updated += 1

    print(f"Summary: updated={updated} skipped={skipped} unresolved={unresolved}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
