"""
Step 1 поиска: bootstrap-скрипт для embeddings.

Когда запускать:
  • Один раз после миграции `migrate_add_search_embeddings.py`, чтобы
    одним батчем покрыть исторические данные (worker нагонит остальное
    через event_outbox).
  • После смены модели (`EMBEDDING_MODEL=...`) — пересчитать вектора
    под новую размерность. Старые строки в `search_embeddings` останутся
    с прежним model_name; новые перезапишут.
  • Ночью на проде, потому что нагрузит CPU 100% на пару минут.

Логика:
  1) Гарантируем что FTS-индекс существует (`search_index_meta`); если нет —
     намекаем запустить `_index_all.py` сначала.
  2) Получаем строки из `search_index_meta`, у которых нет соответствующего
     `search_embeddings` (или content_hash рассинхрон).
  3) Делаем batch-encode'ом (default 32 за раз) — на CPU bge-m3 даёт
     ~5-20 items/sec, e5-base в разы быстрее.
  4) UPSERT.

Запуск:
  python _embed_all.py [--types deal,contract] [--limit 1000] [--batch 32]

ENV:
  EMBEDDING_MODEL — модель для encoder'а (default BAAI/bge-m3)
"""
import argparse
import asyncio
import os
import sys
import time

os.environ.setdefault("SECRET_KEY", "x" * 64)


async def bootstrap(types_filter, limit, batch_size):
    from sqlalchemy import text as sql_text
    from app.database.session import async_session

    # Поллим search_index_meta. Без `_index_all.py` запуска эта таблица
    # будет пустой и embeddings не будут сгенерированы.
    async with async_session() as db:
        # Считаем что есть для embedding'а.
        if types_filter:
            placeholders = ",".join([f":t{i}" for i in range(len(types_filter))])
            params = {f"t{i}": t for i, t in enumerate(types_filter)}
            total_q = sql_text(f"""
                SELECT COUNT(*) FROM search_index_meta m
                LEFT JOIN search_embeddings e
                    ON e.entity_type = m.entity_type AND e.entity_id = m.entity_id
                WHERE m.entity_type IN ({placeholders})
                  AND (e.entity_id IS NULL OR e.content_hash != m.content_hash)
            """)
        else:
            total_q = sql_text("""
                SELECT COUNT(*) FROM search_index_meta m
                LEFT JOIN search_embeddings e
                    ON e.entity_type = m.entity_type AND e.entity_id = m.entity_id
                WHERE e.entity_id IS NULL OR e.content_hash != m.content_hash
            """)
            params = {}
        total = (await db.execute(total_q, params)).scalar() or 0
        if total == 0:
            print("Nothing to embed. Run _index_all.py first or all is up to date.")
            return

        print(f"To embed: {total} rows (model={os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-m3')})")
        if limit and total > limit:
            print(f"  (limited to {limit} this run)")

    # Используем worker'овую логику чтобы не дублировать код.
    # Импортируем модули worker'а напрямую — он использует тот же
    # async_session.
    import embedding_worker as ew

    # Корректируем env-параметры под bootstrap:
    ew.BATCH_SIZE = batch_size
    ew.IDLE_UNLOAD = 9999.0  # не выгружаем модель внутри bootstrap'а

    processed = 0
    started = time.monotonic()
    iters = 0
    async with async_session() as db:
        while True:
            iters += 1
            chunk = await ew._process_outbox_batch(db, batch_size)
            if chunk == 0:
                break
            processed += chunk
            elapsed = time.monotonic() - started
            rate = processed / max(elapsed, 0.001)
            print(f"  iter#{iters}: +{chunk} = {processed}/{total} ({rate:.1f}/s)")
            if limit and processed >= limit:
                print(f"  reached limit {limit}, stopping early")
                break

    elapsed = time.monotonic() - started
    print(f"\n=== DONE in {elapsed:.1f}s ===")
    print(f"Embedded: {processed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap search_embeddings")
    parser.add_argument(
        "--types",
        default="",
        help="Comma-separated entity_types (default: все из search_index_meta)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Лимит строк (default: все)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=32,
        help="Batch size для encode'а (default 32)",
    )
    args = parser.parse_args()
    types_filter = [t.strip() for t in args.types.split(",") if t.strip()] or None

    try:
        asyncio.run(bootstrap(types_filter, args.limit, args.batch))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
