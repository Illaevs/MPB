"""
Bootstrap-скрипт для Step 0 поиска: однократная индексация всех существующих
записей в search_fts.

Когда запускать:
  • Один раз после миграции `migrate_add_search_fts.py` — догнать
    исторические данные, которые не пройдут через `emit_event` хук.
  • Если решили добавить новый entity_type в `EXTRACTORS` — после
    деплоя индексера, чтобы старые записи появились в индексе.
  • Если поиск выдаёт пустые результаты по словам, которые точно есть
    в базе — возможно индекс рассинхронизирован, можно перепрогнать.

Идемпотентность:
  • Использует тот же `index_entity_safe` что и runtime-хук.
  • content_hash проверка → повторный запуск без изменений = no-op.
  • Можно запускать на проде без блокировки (читает по чанкам,
    коммитит каждые 500 записей).

Запуск: python _index_all.py [--types deal,contract,task] [--limit-per-type 1000]
"""
import argparse
import asyncio
import os
import sys
import time
from typing import Optional

os.environ.setdefault("SECRET_KEY", "x" * 64)


async def index_table(db, entity_type: str, model_class, limit: Optional[int] = None) -> dict:
    """Проиндексировать все строки одной таблицы. Возвращает статистику."""
    from sqlalchemy import select
    from app.services.search_indexer import index_entity_safe

    stats = {"total": 0, "indexed": 0, "skipped": 0, "no_content": 0, "errors": 0}

    # Узнаём общее количество для прогресса.
    q = select(model_class)
    if limit:
        q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    stats["total"] = len(rows)

    if not rows:
        print(f"  [{entity_type:25s}] 0 rows")
        return stats

    started = time.monotonic()
    for i, row in enumerate(rows, 1):
        result = await index_entity_safe(db, entity_type, str(row.id))
        if result == "indexed":
            stats["indexed"] += 1
        elif result == "skipped":
            stats["skipped"] += 1
        elif result in ("no_content", "no_extractor"):
            stats["no_content"] += 1
        else:
            stats["errors"] += 1

        # Коммитим пачками по 500 чтобы транзакция не разрасталась.
        if i % 500 == 0:
            await db.commit()
            elapsed = time.monotonic() - started
            rate = i / elapsed
            print(f"  [{entity_type:25s}] {i}/{stats['total']} ({rate:.0f}/s)")

    await db.commit()
    elapsed = time.monotonic() - started
    print(
        f"  [{entity_type:25s}] {stats['total']} rows in {elapsed:.1f}s — "
        f"indexed={stats['indexed']} skipped={stats['skipped']} "
        f"empty={stats['no_content']} errors={stats['errors']}"
    )
    return stats


async def main(types_filter: Optional[list], limit_per_type: Optional[int]):
    from app.database.session import async_session
    from app.services.search_indexer import _get_entity_class, EXTRACTORS

    # Регистрируем индексер-hook: импортируем сам модуль, регистрация
    # происходит side-effect'ом через `register_after_emit_hook`.
    # Опциональный шаг — bootstrap-индексация работает и без hook'а,
    # потому что вызывает index_entity_safe напрямую. Но на всякий
    # случай регистрируем чтобы свежие event-ы во время bootstrap'а
    # тоже подхватились.
    try:
        import app.event_handlers.search_indexer  # noqa: F401
    except ImportError:
        pass  # на старых сборках без event_handlers — игнорим
    # На локалке с event_dispatcher делаем полный discovery:
    try:
        from app.services.event_dispatcher import discover_handlers
        discover_handlers()
    except ImportError:
        pass  # на прод сборке без event_dispatcher — skip

    targets = list(EXTRACTORS.keys())
    if types_filter:
        targets = [t for t in targets if t in types_filter]
    if not targets:
        print("No target entity_types after filter. Available:", list(EXTRACTORS.keys()))
        return

    print(f"Bootstrap indexing: {len(targets)} entity types")
    print(f"Filter: {types_filter or 'ALL'}, limit per type: {limit_per_type or 'ALL'}")
    print()

    total_stats = {"total": 0, "indexed": 0, "skipped": 0, "no_content": 0, "errors": 0}
    started_total = time.monotonic()

    async with async_session() as db:
        for entity_type in targets:
            entity_class = _get_entity_class(entity_type)
            if entity_class is None:
                print(f"  [{entity_type:25s}] SKIP — no model class mapped")
                continue
            try:
                stats = await index_table(db, entity_type, entity_class, limit_per_type)
                for k in total_stats:
                    total_stats[k] += stats[k]
            except Exception as exc:
                print(f"  [{entity_type:25s}] FAILED: {exc}")
                # Откатываем подвисшую транзакцию чтобы следующая таблица
                # стартовала с чистого состояния.
                await db.rollback()

    elapsed_total = time.monotonic() - started_total
    print()
    print(f"=== DONE in {elapsed_total:.1f}s ===")
    print(f"Total rows: {total_stats['total']}")
    print(f"  indexed: {total_stats['indexed']}")
    print(f"  skipped (idempotent): {total_stats['skipped']}")
    print(f"  empty/no extractor:   {total_stats['no_content']}")
    print(f"  errors:               {total_stats['errors']}")


if __name__ == "__main__":
    from typing import Optional  # noqa  (helps stub for index_table)

    parser = argparse.ArgumentParser(description="Bootstrap-индексация search_fts")
    parser.add_argument(
        "--types",
        default="",
        help="Comma-separated entity_types (default: все из EXTRACTORS)",
    )
    parser.add_argument(
        "--limit-per-type",
        type=int,
        default=None,
        help="Лимит строк на тип (для smoke). Без флага — все.",
    )
    args = parser.parse_args()
    types_filter = [t.strip() for t in args.types.split(",") if t.strip()] or None

    try:
        asyncio.run(main(types_filter, args.limit_per_type))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
