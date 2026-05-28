import argparse
import asyncio
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import select, func

from app.database.session import async_session
from app.core.config import settings
from app.models import Company, Deal, OutgoingDocument, Document
from app.routers.outgoing_registry import _normalize_company_key, _sync_document_registry


COL_COMPANY = "Наша компания"
COL_RECIPIENT = "Адресат"
COL_DATE = "Дата письма"
COL_LINK = "Привязка к сделке/лиду"
COL_SUBJECT = "Тема письма"
COL_OUT_NUMBER = "Номер документа"
COL_BODY = "Текст письма"
COL_ATTACH = "Список приложений в письме (пример: 1. Акт № 1 от 17.09.2024 на 1 л. в 1 экз.)"


def _norm_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).strip().lower()
    text = (
        text.replace("«", " ")
        .replace("»", " ")
        .replace('"', " ")
        .replace("“", " ")
        .replace("”", " ")
    )
    text = re.sub(r"\b(ооо|оао|ао|зао|пао|ип|фгбу|гуп|муп|нко|фку)\b", " ", text)
    text = re.sub(r"[^a-z0-9а-я]+", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date(value) -> Optional[date]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _first_non_empty(values: List) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _collect_multiline(values: List) -> str:
    parts = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _select_recipient(values: List) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in {"компания:", "компания"}:
            continue
        return text
    return _first_non_empty(values)


def _extract_number_prefix(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = re.match(r"^(\d+)", str(value).strip())
    if not match:
        return None
    return int(match.group(1))


async def _load_company_map(db) -> Dict[str, List[Tuple[str, str]]]:
    result = await db.execute(select(Company.id, Company.name))
    rows = result.all()
    mapping: Dict[str, List[Tuple[str, str]]] = {}
    for row in rows:
        cid, name = row
        key = _norm_text(name)
        if not key:
            continue
        mapping.setdefault(key, []).append((str(cid), name))
    return mapping


async def _load_deal_map(db) -> Dict[str, List[Tuple[str, str]]]:
    result = await db.execute(select(Deal.id, Deal.title))
    rows = result.all()
    mapping: Dict[str, List[Tuple[str, str]]] = {}
    for row in rows:
        did, title = row
        key = _norm_text(title)
        if not key:
            continue
        mapping.setdefault(key, []).append((str(did), title))
    return mapping


def _match_entity(name: Optional[str], mapping: Dict[str, List[Tuple[str, str]]]) -> Tuple[Optional[str], Optional[str], str]:
    if not name:
        return None, None, "empty"
    needle = _norm_text(name)
    if not needle:
        return None, None, "empty"
    exact = mapping.get(needle)
    if exact:
        return exact[0][0], exact[0][1], "exact"
    candidates = []
    for key, items in mapping.items():
        if needle in key or key in needle:
            for item in items:
                candidates.append((key, item))
    if not candidates:
        return None, None, "missing"
    # pick the closest length match
    candidates.sort(key=lambda item: abs(len(item[0]) - len(needle)))
    return candidates[0][1][0], candidates[0][1][1], "partial"


async def _get_next_global_seq(db) -> int:
    result = await db.execute(select(func.max(OutgoingDocument.outgoing_number_seq)))
    max_value = result.scalar()
    if max_value is None:
        return settings.OUTGOING_NUMBER_START
    return int(max_value) + 1


async def main(path: str, dry_run: bool = False) -> None:
    df = pd.read_excel(path, sheet_name=0)
    required = {COL_COMPANY, COL_RECIPIENT, COL_DATE, COL_LINK, COL_SUBJECT, COL_OUT_NUMBER, COL_BODY, COL_ATTACH}
    missing = required.difference(df.columns)
    if missing:
        raise SystemExit(f"Missing columns: {', '.join(sorted(missing))}")

    start_mask = df[COL_OUT_NUMBER].notna() | df[COL_COMPANY].notna() | df[COL_DATE].notna()
    df["_group_id"] = start_mask.cumsum()
    groups = [g for _, g in df.groupby("_group_id") if not g.empty]

    async with async_session() as db:
        company_map = await _load_company_map(db)
        deal_map = await _load_deal_map(db)
        next_global_seq = await _get_next_global_seq(db)

        created = 0
        skipped_existing = 0
        missing_recipient = 0
        missing_deal = 0
        for group in groups:
            values = group.to_dict(orient="list")

            our_company_raw = _first_non_empty(values[COL_COMPANY])
            if not our_company_raw:
                continue
            our_company_key = _normalize_company_key(our_company_raw)

            recipient_raw = _select_recipient(values[COL_RECIPIENT])
            recipient_id, recipient_name, recipient_status = _match_entity(recipient_raw, company_map)
            if not recipient_id:
                missing_recipient += 1
                continue

            letter_date = _parse_date(_first_non_empty(values[COL_DATE]))
            if not letter_date:
                continue

            subject = _first_non_empty(values[COL_SUBJECT]) or "Исходящее письмо"
            outgoing_display = _first_non_empty(values[COL_OUT_NUMBER])
            if not outgoing_display:
                continue

            deal_hint = _first_non_empty(values[COL_LINK])
            deal_id, deal_title, deal_status = _match_entity(deal_hint, deal_map)
            if deal_status == "missing":
                missing_deal += 1
                deal_id = None

            body = _collect_multiline(values[COL_BODY])
            attachments = _collect_multiline(values[COL_ATTACH])

            outgoing_number = f"{our_company_key}:{outgoing_display}"

            existing = await db.execute(
                select(OutgoingDocument).where(OutgoingDocument.outgoing_number == outgoing_number)
            )
            if existing.scalar_one_or_none():
                skipped_existing += 1
                continue

            company_seq = _extract_number_prefix(outgoing_display)

            if dry_run:
                created += 1
                continue

            document = await OutgoingDocument.create(
                db,
                outgoing_number_seq=next_global_seq,
                outgoing_number=outgoing_number,
                our_company_key=our_company_key,
                outgoing_number_company_seq=company_seq,
                recipient_company_id=recipient_id,
                deal_id=deal_id,
                letter_date=letter_date,
                subject=subject,
                body=body,
                attachments_list=attachments,
                status="draft",
            )
            next_global_seq += 1
            try:
                await _sync_document_registry(db, document)
            except Exception:
                pass
            created += 1

        print(
            "Summary:",
            f"created={created}",
            f"skipped_existing={skipped_existing}",
            f"missing_recipient={missing_recipient}",
            f"missing_deal={missing_deal}",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to lists5.xlsx")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.path, dry_run=args.dry_run))
