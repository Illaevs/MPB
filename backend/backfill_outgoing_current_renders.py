#!/usr/bin/env python3
"""
Backfill current render DOCX/PDF files for outgoing registry documents.

Strategy:
1. If document has a latest version and the document was not modified after it,
   restore current render from that version.
2. Otherwise regenerate current render from the current document body using the
   same DOCX template generator as the frontend.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import select

from app.database.session import async_session
from app.models import Company, OutgoingDocument
from app.routers.outgoing_registry import (
    _convert_docx_to_pdf_bytes,
    _display_outgoing_number,
    _document_has_changes_after_latest_version,
    _get_latest_version_bundle,
    _read_optional_storage_file,
    _store_current_render_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RENDER_SCRIPT_PATH = FRONTEND_DIR / "scripts" / "render_outgoing_docx.mjs"


async def _build_render_payload(db, document: OutgoingDocument) -> dict:
    recipient = await Company.get_by_id(db, str(document.recipient_company_id))
    display_number = _display_outgoing_number(document.outgoing_number) or document.outgoing_number
    return {
        "id": str(document.id),
        "outgoing_number": display_number or "",
        "our_company_key": document.our_company_key or "normbud",
        "letter_date": document.letter_date.isoformat() if document.letter_date else "",
        "subject": document.subject or "",
        "body": document.body or "",
        "attachments_list": document.attachments_list or "",
        "recipient_company_name": recipient.name if recipient else "",
        "recipient_short_name": document.recipient_short_name or "",
        "recipient_to_name": document.recipient_to_name or "",
        "recipient_appeal": document.recipient_appeal or "",
        "recipient_eio": document.recipient_eio or "",
        "recipient_salutation": document.recipient_salutation or "",
    }


def _render_docx_via_node(payload: dict) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        input_path = tmp_path / "outgoing.json"
        output_path = tmp_path / "outgoing.docx"
        input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            ["node", str(RENDER_SCRIPT_PATH), str(input_path), str(output_path)],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or not output_path.exists():
            raise RuntimeError(
                "Node DOCX renderer failed:\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return output_path.read_bytes()


async def backfill_current_renders():
    stats = {
        "total": 0,
        "restored_from_version": 0,
        "regenerated": 0,
        "failed": 0,
    }
    async with async_session() as db:
        result = await db.execute(select(OutgoingDocument).order_by(OutgoingDocument.created_at.asc()))
        documents = result.scalars().all()
        stats["total"] = len(documents)
        print(f"Outgoing documents to process: {stats['total']}")

        for index, document in enumerate(documents, start=1):
            doc_label = f"{document.outgoing_number} [{document.id}]"
            try:
                latest_version, latest_docx, latest_pdf = await _get_latest_version_bundle(db, str(document.id))
                can_restore_from_version = latest_version and not _document_has_changes_after_latest_version(document, latest_version)
                if can_restore_from_version:
                    latest_docx_bytes = await _read_optional_storage_file(latest_docx)
                    latest_pdf_bytes = await _read_optional_storage_file(latest_pdf)
                    if latest_docx_bytes and latest_pdf_bytes:
                        await _store_current_render_files(db, document, latest_docx_bytes, latest_pdf_bytes)
                        stats["restored_from_version"] += 1
                        print(f"[{index}/{stats['total']}] restored from latest version: {doc_label}")
                        continue

                payload = await _build_render_payload(db, document)
                docx_bytes = _render_docx_via_node(payload)
                pdf_bytes = _convert_docx_to_pdf_bytes(docx_bytes)
                if not pdf_bytes:
                    raise RuntimeError("PDF conversion returned empty result")
                await _store_current_render_files(db, document, docx_bytes, pdf_bytes)
                stats["regenerated"] += 1
                print(f"[{index}/{stats['total']}] regenerated current render: {doc_label}")
            except Exception as exc:
                stats["failed"] += 1
                print(f"[{index}/{stats['total']}] FAILED: {doc_label}\n{exc}\n")

    print(
        "Done. "
        f"restored_from_version={stats['restored_from_version']}, "
        f"regenerated={stats['regenerated']}, "
        f"failed={stats['failed']}"
    )


if __name__ == "__main__":
    asyncio.run(backfill_current_renders())
