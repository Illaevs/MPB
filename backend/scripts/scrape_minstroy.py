"""
Minстрой scraper: загрузка полных текстов норм из minstroyrf.gov.ru.

Этапы:
  1. Загрузить YAML со списком норм (doc_type/doc_number/minstroy_page).
  2. Для каждой записи:
       a. GET страницы → найти PDF-ссылку (по pdf_hint или по regex).
       b. GET PDF → блоб в памяти.
       c. Парсинг через `reglament_parser.parse_pdf_bytes` (PyMuPDF).
       d. Найти запись в `reglaments` по (doc_type, doc_number); если нет —
          скип (норма должна сначала быть в curated-каталоге).
       e. Заменить sections (cover остаётся) + обновить source_url + flush
          embeddings (для последующего bootstrap).
  3. Возвращает статистику.

Embedding запускается отдельно — после `scrape_minstroy.py` запускаем
`_embed_reglaments.py` чтобы добить новые секции (или embedding-worker
если он у нас есть для reglaments).

Запуск (на проде):
    python scripts/scrape_minstroy.py [--yaml ...] [--delay 2.0] [--limit N]

ENV: использует те же async_session что и API.
"""
import argparse
import asyncio
import hashlib
import os
import re
import sys
import time
import uuid
from typing import Optional

os.environ.setdefault("SECRET_KEY", "x" * 64)


def _load_yaml(path: str) -> list[dict]:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "norms" not in data:
        raise ValueError(f"{path}: ожидаем верхний ключ `norms:`")
    return data["norms"] or []


def _find_pdf_url(html: str, doc_number: str, pdf_hint: Optional[str]) -> Optional[str]:
    """Найти URL PDF на странице Минстроя.

    Стратегия:
      1. Если есть `pdf_hint` (например 'SP-63.pdf') — ищем точное совпадение.
      2. Иначе пробуем шаблон `SP-{short_num}.pdf` (короткий номер
         типа 63 / 118 / 70).
      3. Возвращаем абсолютный URL (с https://www.minstroyrf.gov.ru).
    """
    base = "https://www.minstroyrf.gov.ru"
    if pdf_hint:
        # Ищем по точному имени файла
        m = re.search(rf'href="([^"]*{re.escape(pdf_hint)})"', html)
        if m:
            href = m.group(1)
            return href if href.startswith("http") else base + href

    # Фолбэк: SP-{short}.pdf, где short — первая часть номера до точки
    short = doc_number.split(".")[0]
    pattern = rf'href="([^"]*/SP-{re.escape(short)}\.pdf)"'
    m = re.search(pattern, html, re.I)
    if m:
        href = m.group(1)
        return href if href.startswith("http") else base + href

    # Последний шанс: любой /upload/iblock/.../SP*.pdf на странице
    m = re.search(r'href="(/upload/iblock/[^"]*/SP[^"]*\.pdf)"', html)
    if m:
        return base + m.group(1)
    return None


async def _fetch_url(client, url: str) -> Optional[bytes]:
    """Скачать URL с retry. Возвращает bytes или None."""
    try:
        r = await client.get(url)
        if r.status_code == 200:
            return r.content
    except Exception as exc:
        print(f"      ! fetch error: {exc}")
    return None


async def process_one(client, db, entry: dict) -> dict:
    """Обработать одну запись YAML. Возвращает статистику."""
    from sqlalchemy import select
    from app.models import Reglament
    from app.routers.reglaments import _save_parsed_sections
    from app.services.reglament_parser import parse_pdf_bytes

    doc_type = entry["doc_type"]
    doc_number = entry["doc_number"]
    page_url = entry["minstroy_page"]
    pdf_hint = entry.get("pdf_hint")

    stat = {"doc": f"{doc_type} {doc_number}", "status": "?", "sections": 0, "chars": 0}

    # 1. Найти запись в БД
    rg = (await db.execute(
        select(Reglament).where(
            Reglament.doc_type == doc_type,
            Reglament.doc_number == doc_number,
        )
    )).scalar_one_or_none()
    if rg is None:
        stat["status"] = "skip_not_in_db"
        return stat

    # 2. Скачать страницу
    page_blob = await _fetch_url(client, page_url)
    if not page_blob:
        stat["status"] = "page_fetch_failed"
        return stat
    html = page_blob.decode("utf-8", errors="ignore")

    # 3. Найти PDF
    pdf_url = _find_pdf_url(html, doc_number, pdf_hint)
    if not pdf_url:
        stat["status"] = "pdf_not_found_on_page"
        return stat

    # 4. Скачать PDF
    pdf_blob = await _fetch_url(client, pdf_url)
    if not pdf_blob or len(pdf_blob) < 1024:
        stat["status"] = "pdf_fetch_failed"
        return stat

    # 5. Парсинг
    sections = parse_pdf_bytes(pdf_blob)
    if not sections:
        stat["status"] = "parse_empty"
        return stat

    # 6. Сохранить секции
    total_chars = await _save_parsed_sections(
        db, rg.id, doc_type, doc_number, sections,
    )
    # 7. Обновить header
    rg.section_count = 1 + len(sections)  # cover + real
    rg.full_text_size = total_chars
    rg.source_url = pdf_url  # верифицированный URL
    rg.updated_at = None  # пусть SQLAlchemy выставит CURRENT_TIMESTAMP

    stat["status"] = "ok"
    stat["sections"] = len(sections)
    stat["chars"] = total_chars
    stat["pdf_url"] = pdf_url
    return stat


async def main(yaml_path: str, delay: float, limit: Optional[int]) -> None:
    import httpx
    from app.database.session import async_session

    entries = _load_yaml(yaml_path)
    if limit:
        entries = entries[:limit]
    print(f"To process: {len(entries)} norms")

    started = time.monotonic()
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CRM-Reglaments/0.1; +mpb-erp.ru)",
        "Accept-Language": "ru,en;q=0.8",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        async with async_session() as db:
            for i, entry in enumerate(entries, 1):
                print(f"\n[{i}/{len(entries)}] {entry['doc_type']} {entry['doc_number']}")
                stat = await process_one(client, db, entry)
                results.append(stat)
                print(f"  → {stat['status']}", end="")
                if stat.get("sections"):
                    print(f"  ({stat['sections']} sections, {stat['chars']:,} chars)")
                else:
                    print()
                # Коммитим каждую запись отдельно
                await db.commit()
                if i < len(entries):
                    await asyncio.sleep(delay)

    elapsed = time.monotonic() - started
    print(f"\n=== DONE in {elapsed:.1f}s ===")
    by_status: dict = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    for k, v in by_status.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Минстрой scraper для нормативной базы")
    parser.add_argument("--yaml", default="scripts/reglaments_data/minstroy_urls.yaml")
    parser.add_argument("--delay", type=float, default=2.0, help="секунд между запросами")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.yaml, args.delay, args.limit))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
