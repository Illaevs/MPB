#!/usr/bin/env python3
"""
Regenerate current DOCX/PDF render for specific outgoing documents from their
current DB body and company template.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import select

from app.database.session import async_session
from app.models import Company, OutgoingDocument
from app.routers.outgoing_registry import (
    _convert_docx_to_pdf_bytes,
    _display_outgoing_number,
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


async def regenerate(ids: list[str]):
    async with async_session() as db:
        for doc_id in ids:
            document = (
                await db.execute(select(OutgoingDocument).where(OutgoingDocument.id == doc_id))
            ).scalar_one_or_none()
            if not document:
                print("NOT FOUND", doc_id)
                continue
            payload = await _build_render_payload(db, document)
            docx_bytes = _render_docx_via_node(payload)
            pdf_bytes = _convert_docx_to_pdf_bytes(docx_bytes)
            if not pdf_bytes:
                raise RuntimeError(f"PDF conversion returned empty result for {doc_id}")
            await _store_current_render_files(db, document, docx_bytes, pdf_bytes)
            print("REGENERATED", doc_id, document.outgoing_number, document.our_company_key)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: regenerate_outgoing_current_for_docs.py <doc_id> [<doc_id> ...]")
    asyncio.run(regenerate(sys.argv[1:]))
