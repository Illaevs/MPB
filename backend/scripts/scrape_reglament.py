"""
Reglaments Phase 0/1: загрузка нормативного документа в БД.

Источники:
  • `--json <file>` — структурированный JSON (наш формат, см.
    reglaments_data/sp-63-13330-2018.json)
  • `--html <file>` — локальный HTML файл со страницы docs.cntd.ru
    (Phase 1: пишем парсер; пока — JSON-only)
  • `--url <url>` — fetch и парсинг (Phase 1)

JSON-формат (`reglaments_data/*.json`):
  {
    "doc_type": "СП",
    "doc_number": "63.13330.2018",
    "title": "...",
    "full_title": "...",
    "status": "actual",
    "effective_date": "2019-06-20",
    "discipline_tags": "КЖ,КМ",
    "source_url": "...",
    "page_count": 158,
    "sections": [
      {"section_number": "5.4.2", "section_title": "...", "content": "..."},
      ...
    ]
  }

Запуск:
  python scripts/scrape_reglament.py --json scripts/reglaments_data/sp-63-13330-2018.json

Идемпотентность: документ с тем же (doc_type, doc_number) перезаписывается —
сначала удаляются старые секции (CASCADE), потом вставляются новые.
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime

os.environ.setdefault("SECRET_KEY", "x" * 64)


async def import_reglament(data: dict) -> dict:
    """Импорт одного документа из словаря. Возвращает статистику."""
    from sqlalchemy import select, text
    from app.database.session import async_session
    from app.models import Reglament, ReglamentSection

    doc_type = data["doc_type"]
    doc_number = data["doc_number"]
    sections_data = data.get("sections", [])

    if not sections_data:
        raise ValueError(f"{doc_type} {doc_number}: no sections")

    async with async_session() as db:
        # Находим существующий или создаём новый header.
        existing = (await db.execute(
            select(Reglament).where(
                Reglament.doc_type == doc_type,
                Reglament.doc_number == doc_number,
            )
        )).scalar_one_or_none()

        if existing:
            r_id = existing.id
            # Сносим старые секции через FK CASCADE (просто удаляем header
            # с прицепом — но это слишком радикально, теряем id).
            # Лучше — обновить поля и пересоздать секции отдельным DELETE.
            await db.execute(text(
                "DELETE FROM reglament_sections WHERE reglament_id = :rid"
            ), {"rid": r_id})
            # Очищаем FTS-индекс этого документа.
            await db.execute(text(
                "DELETE FROM reglament_fts WHERE reglament_id = :rid"
            ), {"rid": r_id})
            # Очищаем embeddings (пересчитаем позже через bootstrap).
            await db.execute(text(
                "DELETE FROM reglament_embeddings WHERE reglament_id = :rid"
            ), {"rid": r_id})
            # Обновляем поля header'а.
            existing.title = data["title"]
            existing.full_title = data.get("full_title")
            existing.status = data.get("status", "actual")
            existing.discipline_tags = data.get("discipline_tags")
            existing.source_url = data.get("source_url")
            existing.page_count = data.get("page_count")
            if data.get("effective_date"):
                existing.effective_date = datetime.strptime(
                    data["effective_date"], "%Y-%m-%d"
                ).date()
            r = existing
            action = "updated"
        else:
            r = Reglament(
                id=str(uuid.uuid4()),
                doc_type=doc_type,
                doc_number=doc_number,
                title=data["title"],
                full_title=data.get("full_title"),
                status=data.get("status", "actual"),
                discipline_tags=data.get("discipline_tags"),
                source_url=data.get("source_url"),
                page_count=data.get("page_count"),
            )
            if data.get("effective_date"):
                r.effective_date = datetime.strptime(
                    data["effective_date"], "%Y-%m-%d"
                ).date()
            db.add(r)
            await db.flush()
            r_id = r.id
            action = "created"

        # Вставляем секции + одновременно индексируем в reglament_fts.
        total_chars = 0
        for idx, sd in enumerate(sections_data):
            sec_id = str(uuid.uuid4())
            content = sd["content"] or ""
            char_count = len(content)
            total_chars += char_count

            sec = ReglamentSection(
                id=sec_id,
                reglament_id=r_id,
                section_number=sd.get("section_number"),
                section_title=sd.get("section_title"),
                content=content,
                order_idx=idx,
                char_count=char_count,
            )
            db.add(sec)

            # FTS5 — отдельный INSERT, не через ORM.
            await db.execute(text("""
                INSERT INTO reglament_fts
                    (section_id, reglament_id, doc_number, doc_type,
                     section_number, section_title, content)
                VALUES
                    (:sid, :rid, :dn, :dt, :sn, :st, :ct)
            """), {
                "sid": sec_id, "rid": r_id,
                "dn": doc_number, "dt": doc_type,
                "sn": sd.get("section_number") or "",
                "st": sd.get("section_title") or "",
                "ct": content,
            })

            # content_hash для embedding-идемпотентности.
            h = hashlib.sha256()
            h.update((sd.get("section_title") or "").encode("utf-8"))
            h.update(b"\x00")
            h.update(content.encode("utf-8"))
            await db.execute(text("""
                INSERT INTO reglament_index_meta (section_id, content_hash, last_indexed_at)
                VALUES (:sid, :hash, CURRENT_TIMESTAMP)
                ON CONFLICT(section_id) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    last_indexed_at = CURRENT_TIMESTAMP
            """), {"sid": sec_id, "hash": h.hexdigest()})

        # Статистика на header.
        r.section_count = len(sections_data)
        r.full_text_size = total_chars

        await db.commit()

        return {
            "action": action,
            "reglament_id": r_id,
            "doc_type": doc_type,
            "doc_number": doc_number,
            "sections_count": len(sections_data),
            "total_chars": total_chars,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Импорт нормативного документа в БД")
    parser.add_argument("--json", help="Путь к JSON-файлу со структурой документа")
    parser.add_argument("--html", help="Локальный HTML файл (Phase 1, не реализовано)")
    parser.add_argument("--url", help="URL для fetch (Phase 1, не реализовано)")
    args = parser.parse_args()

    if not args.json:
        if args.html or args.url:
            print("HTML/URL парсер будет в Phase 1. Сейчас доступен только --json.")
            return 2
        parser.print_help()
        return 2

    with open(args.json, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = asyncio.run(import_reglament(data))
    print(f"[{result['action']}] {result['doc_type']} {result['doc_number']}")
    print(f"  reglament_id: {result['reglament_id']}")
    print(f"  sections:     {result['sections_count']}")
    print(f"  total chars:  {result['total_chars']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
