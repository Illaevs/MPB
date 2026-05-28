"""
Reglaments Phase 1: batch-импорт списка норм из curated YAML.

Два режима:
  --headers-only (default):
      Только метаданные (doc_type, doc_number, title, status, ...) — без
      содержимого секций. Каталог /reglaments сразу заполняется ~60+ норм,
      их можно искать по номеру и названию (FTS5 над header'ами).
      Сам контент норм потом добавляется через UI (Phase 3) либо
      через `scrape_reglament.py --json <file>` для конкретной нормы.

  --with-content (требует httpx + beautifulsoup4):
      Дополнительно идёт по source_url, парсит HTML и создаёт секции.
      Источник по умолчанию — docs.cntd.ru (требует rate-limit). Не
      гарантировано: paywall / изменения вёрстки / IP-блок могут вернуть
      0 секций — в этом случае норма сохраняется как header-only.

Запуск:
    python scripts/scrape_reglaments_batch.py \
        --yaml scripts/reglaments_data/curated_norms.yaml \
        [--with-content] [--limit N] [--dry-run] [--force]

Идемпотентность: норма с тем же (doc_type, doc_number) пропускается;
с `--force` — перезаписывается.
"""
import argparse
import asyncio
import hashlib
import os
import sys
import time
import uuid
from datetime import datetime

os.environ.setdefault("SECRET_KEY", "x" * 64)


def _load_yaml(path: str) -> list[dict]:
    """Минимальный yaml-loader: используем PyYAML если установлен, иначе
    жалуемся (не делаем самопальный парсер — он будет хрупким на
    кириллице/датах/комментариях)."""
    try:
        import yaml  # PyYAML
    except ImportError:
        print(
            "ERROR: PyYAML not installed. Install:\n"
            "  pip install pyyaml\n"
            "или используй scrape_reglament.py --json <one-file>"
        )
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "norms" not in data:
        raise ValueError(f"{path}: ожидаем верхний ключ `norms:` со списком")
    return data["norms"] or []


async def _upsert_header_only(db, entry: dict, *, force: bool) -> str:
    """Создать/обновить Reglament из YAML-entry. Возвращает action:
    'created' / 'updated' / 'skipped'.

    Дополнительно создаём `cover-section` — синтетическую секцию #0 с
    full_title + дисциплинами. Это нужно чтобы header-only документы
    (без реального контента) находились через `/reglaments/search` —
    `reglament_fts` индексирует только секции, и без cover-section
    запрос «арматура» не найдёт СП 16.13330 пока контент не загружен.
    """
    from sqlalchemy import select, text as sql_text
    from app.models import Reglament, ReglamentSection

    doc_type = entry["doc_type"]
    doc_number = entry["doc_number"]

    existing = (await db.execute(
        select(Reglament).where(
            Reglament.doc_type == doc_type,
            Reglament.doc_number == doc_number,
        )
    )).scalar_one_or_none()

    if existing and not force:
        return "skipped"

    if existing:
        existing.title = entry.get("title", existing.title)
        existing.full_title = entry.get("full_title", existing.full_title)
        existing.status = entry.get("status", existing.status)
        existing.discipline_tags = entry.get("discipline_tags", existing.discipline_tags)
        existing.source_url = entry.get("source_url", existing.source_url)
        existing.page_count = entry.get("page_count", existing.page_count)
        if entry.get("effective_date"):
            existing.effective_date = _parse_date(entry["effective_date"])
        await _ensure_cover_section(db, existing.id, doc_type, doc_number, entry)
        return "updated"

    rg = Reglament(
        id=str(uuid.uuid4()),
        doc_type=doc_type,
        doc_number=doc_number,
        title=entry["title"],
        full_title=entry.get("full_title"),
        status=entry.get("status", "actual"),
        discipline_tags=entry.get("discipline_tags"),
        source_url=entry.get("source_url"),
        page_count=entry.get("page_count"),
        section_count=1,  # cover-section
        full_text_size=0,
    )
    if entry.get("effective_date"):
        rg.effective_date = _parse_date(entry["effective_date"])
    db.add(rg)
    await db.flush()
    await _ensure_cover_section(db, rg.id, doc_type, doc_number, entry)
    return "created"


async def _ensure_cover_section(db, reglament_id: str, doc_type: str, doc_number: str, entry: dict) -> None:
    """Создать/обновить синтетическую секцию-обложку для FTS-поиска.

    section_number = '0', section_title = краткий title, content =
    full_title + дисциплины + ключевые слова. Это идёт в reglament_fts.
    Реальные секции (если потом загрузят через scrape_reglament.py)
    идут отдельным порядком (order_idx >= 1).
    """
    from sqlalchemy import text as sql_text
    from app.models import ReglamentSection

    # Удаляем старую cover (если была)
    await db.execute(sql_text(
        "DELETE FROM reglament_sections WHERE reglament_id = :rid AND section_number = '0'"
    ), {"rid": reglament_id})
    await db.execute(sql_text(
        "DELETE FROM reglament_fts WHERE reglament_id = :rid AND section_number = '0'"
    ), {"rid": reglament_id})

    cover_id = str(uuid.uuid4())
    title = entry["title"]
    full_title = entry.get("full_title") or title
    disciplines = entry.get("discipline_tags") or ""
    # Контент cover-секции: полное название + дисциплины.
    # Для FTS — это даёт поиск по «бетонные конструкции», «огнестойкость» и т.п.
    parts = [full_title]
    if disciplines:
        parts.append(f"Дисциплины: {disciplines}")
    parts.append(f"{doc_type} {doc_number}")
    content = "\n".join(parts)

    sec = ReglamentSection(
        id=cover_id,
        reglament_id=reglament_id,
        section_number="0",
        section_title=title,
        content=content,
        order_idx=0,
        char_count=len(content),
    )
    db.add(sec)
    await db.execute(sql_text("""
        INSERT INTO reglament_fts
            (section_id, reglament_id, doc_number, doc_type,
             section_number, section_title, content)
        VALUES (:sid, :rid, :dn, :dt, :sn, :st, :ct)
    """), {
        "sid": cover_id, "rid": reglament_id, "dn": doc_number, "dt": doc_type,
        "sn": "0", "st": title, "ct": content,
    })
    h = hashlib.sha256()
    h.update(title.encode("utf-8"))
    h.update(b"\x00")
    h.update(content.encode("utf-8"))
    await db.execute(sql_text("""
        INSERT INTO reglament_index_meta (section_id, content_hash, last_indexed_at)
        VALUES (:sid, :hash, CURRENT_TIMESTAMP)
        ON CONFLICT(section_id) DO UPDATE SET
            content_hash = excluded.content_hash,
            last_indexed_at = CURRENT_TIMESTAMP
    """), {"sid": cover_id, "hash": h.hexdigest()})


def _parse_date(v):
    from datetime import date
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return datetime.strptime(v, "%Y-%m-%d").date()
    return None


async def _fetch_sections_from_url(url: str) -> list[dict]:
    """Опциональная HTTP-загрузка содержимого. Best-effort: если HTML не
    парсится — возвращаем []. Требует httpx + beautifulsoup4."""
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return []
    headers = {
        # Минимально-вежливый UA. docs.cntd.ru может ограничить из коробки.
        "User-Agent": "Mozilla/5.0 (compatible; CRM-Reglaments/0.1; +contact@mpb-erp.ru)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru,en;q=0.8",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                return []
            html = r.text
    except Exception:
        return []

    # Парсер для docs.cntd.ru: документ структурирован под `div.doc-body`,
    # секции — `div.content_section` или просто заголовки h1-h4 + параграфы.
    # Если эвристика не сработала — возвращаем [] (норма остаётся header-only).
    soup = BeautifulSoup(html, "html.parser")

    container = (
        soup.find("div", class_="doc-body")
        or soup.find("div", class_="doc-content")
        or soup.find("div", id="content")
        or soup.find("article")
        or soup.body
    )
    if container is None:
        return []

    sections: list[dict] = []
    current = {"section_number": "1", "section_title": "Введение", "content": ""}
    order = 0
    for node in container.find_all(["h1", "h2", "h3", "h4", "p"]):
        text = node.get_text(separator=" ", strip=True)
        if not text:
            continue
        if node.name in ("h1", "h2", "h3", "h4"):
            # Закрываем текущую секцию если в ней что-то накопилось
            if current["content"].strip():
                sections.append(_normalize_section(current, order))
                order += 1
            current = _detect_section_number(text)
        else:
            current["content"] += text + "\n"
    if current["content"].strip():
        sections.append(_normalize_section(current, order))

    # Filter to those with meaningful content (>=80 chars)
    sections = [s for s in sections if len(s["content"]) >= 80]
    return sections


def _detect_section_number(heading: str) -> dict:
    """Эвристически отделить номер раздела от заголовка: '5.4.2 Защитный
    слой бетона' → {section_number: '5.4.2', section_title: 'Защитный слой...'}.
    """
    import re
    m = re.match(r"^([\d\.]+|Приложение\s+[А-ЯA-Z\d]+)\s+(.+)$", heading)
    if m:
        return {"section_number": m.group(1), "section_title": m.group(2).strip(), "content": ""}
    return {"section_number": None, "section_title": heading, "content": ""}


def _normalize_section(s: dict, order: int) -> dict:
    out = dict(s)
    out["order_idx"] = order
    out["char_count"] = len(out["content"])
    return out


async def _save_sections(db, reglament_id: str, doc_type: str, doc_number: str, sections: list[dict]) -> int:
    """Сохранить секции + проиндексировать в reglament_fts. Возвращает кол-во."""
    from sqlalchemy import text
    from app.models import ReglamentSection

    # Удалить старые секции (force-режим)
    await db.execute(text("DELETE FROM reglament_sections WHERE reglament_id = :rid"), {"rid": reglament_id})
    await db.execute(text("DELETE FROM reglament_fts WHERE reglament_id = :rid"), {"rid": reglament_id})
    await db.execute(text("DELETE FROM reglament_embeddings WHERE reglament_id = :rid"), {"rid": reglament_id})

    total_chars = 0
    for s in sections:
        sec_id = str(uuid.uuid4())
        content = s["content"]
        total_chars += s["char_count"]
        sec = ReglamentSection(
            id=sec_id,
            reglament_id=reglament_id,
            section_number=s.get("section_number"),
            section_title=s.get("section_title"),
            content=content,
            order_idx=s.get("order_idx", 0),
            char_count=s.get("char_count", 0),
        )
        db.add(sec)
        await db.execute(text("""
            INSERT INTO reglament_fts
                (section_id, reglament_id, doc_number, doc_type,
                 section_number, section_title, content)
            VALUES (:sid, :rid, :dn, :dt, :sn, :st, :ct)
        """), {
            "sid": sec_id, "rid": reglament_id, "dn": doc_number, "dt": doc_type,
            "sn": s.get("section_number") or "",
            "st": s.get("section_title") or "",
            "ct": content,
        })
        h = hashlib.sha256()
        h.update((s.get("section_title") or "").encode("utf-8"))
        h.update(b"\x00")
        h.update(content.encode("utf-8"))
        await db.execute(text("""
            INSERT INTO reglament_index_meta (section_id, content_hash, last_indexed_at)
            VALUES (:sid, :hash, CURRENT_TIMESTAMP)
            ON CONFLICT(section_id) DO UPDATE SET
                content_hash = excluded.content_hash,
                last_indexed_at = CURRENT_TIMESTAMP
        """), {"sid": sec_id, "hash": h.hexdigest()})

    return total_chars


async def main(args):
    from app.database.session import async_session
    from sqlalchemy import select
    from app.models import Reglament

    entries = _load_yaml(args.yaml)
    if args.limit:
        entries = entries[: args.limit]
    print(f"Loaded {len(entries)} norms from {args.yaml}")
    if args.dry_run:
        for e in entries:
            print(f"  [{e['doc_type']:5s}] {e['doc_number']:24s} — {e['title'][:60]}")
        return

    stats = {"created": 0, "updated": 0, "skipped": 0, "scraped": 0, "scrape_failed": 0}
    started = time.monotonic()

    async with async_session() as db:
        for i, entry in enumerate(entries, 1):
            try:
                action = await _upsert_header_only(db, entry, force=args.force)
                stats[action] = stats.get(action, 0) + 1

                # Если запрошен content и норма создалась/обновилась — пробуем scrape
                if args.with_content and action in ("created", "updated") and entry.get("source_url"):
                    rg = (await db.execute(
                        select(Reglament).where(
                            Reglament.doc_type == entry["doc_type"],
                            Reglament.doc_number == entry["doc_number"],
                        )
                    )).scalar_one_or_none()
                    if rg:
                        print(f"  [{i:3d}/{len(entries)}] scraping {entry['source_url']} ...")
                        sections = await _fetch_sections_from_url(entry["source_url"])
                        if sections:
                            total = await _save_sections(
                                db, rg.id, entry["doc_type"], entry["doc_number"], sections
                            )
                            rg.section_count = len(sections)
                            rg.full_text_size = total
                            stats["scraped"] += 1
                            print(f"      → {len(sections)} sections, {total} chars")
                        else:
                            stats["scrape_failed"] += 1
                            print(f"      → no sections parsed (header-only)")
                        # Вежливая пауза — не молотить docs.cntd.ru
                        await asyncio.sleep(args.delay)
                else:
                    if i % 20 == 0 or i == len(entries):
                        print(f"  [{i:3d}/{len(entries)}] {action}")
            except Exception as exc:
                print(f"  [{i:3d}/{len(entries)}] FAILED {entry.get('doc_number')}: {exc}")
                stats["failed"] = stats.get("failed", 0) + 1

            # Коммит пачками по 20 — чтобы при сбое не терять прогресс
            if i % 20 == 0:
                await db.commit()

        await db.commit()

    elapsed = time.monotonic() - started
    print()
    print(f"=== DONE in {elapsed:.1f}s ===")
    for k, v in stats.items():
        print(f"  {k:15s} {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-импорт нормативной базы")
    parser.add_argument("--yaml", default="scripts/reglaments_data/curated_norms.yaml")
    parser.add_argument("--with-content", action="store_true",
                        help="Дополнительно скрапить полный текст с docs.cntd.ru")
    parser.add_argument("--limit", type=int, default=None,
                        help="Лимит норм для smoke (default — все из YAML)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Показать что будет залито, но ничего не писать")
    parser.add_argument("--force", action="store_true",
                        help="Перезаписать существующие нормы (default — пропускать)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Задержка между HTTP-запросами в секундах (default 1.5)")
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
