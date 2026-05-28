"""
Reglaments Phase 1: bootstrap embeddings для нормативной базы.

Берёт все секции из `reglament_sections` у которых ещё нет записи в
`reglament_embeddings` (либо content_hash расходится, либо модель сменилась),
прогоняет batched через bge-m3, UPSERT'ит.

Запуск (на CPU bge-m3 даёт ~5-15 items/s):
    python _embed_reglaments.py [--batch 32] [--limit N]

ENV: те же что у `embedding_worker.py` (EMBEDDING_MODEL и т.д.).
"""
import argparse
import asyncio
import os
import sys
import time
import uuid

os.environ.setdefault("SECRET_KEY", "x" * 64)


async def bootstrap(batch_size: int, limit: int | None) -> None:
    from sqlalchemy import text
    from app.database.session import async_session

    MODEL_ID = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")

    async with async_session() as db:
        total = (await db.execute(text("""
            SELECT COUNT(*) FROM reglament_index_meta m
            LEFT JOIN reglament_embeddings e ON e.section_id = m.section_id
            WHERE e.section_id IS NULL
               OR e.content_hash != m.content_hash
               OR e.model_name != :model
        """), {"model": MODEL_ID})).scalar() or 0
        if total == 0:
            print("Nothing to embed.")
            return
        print(f"To embed: {total} sections (model={MODEL_ID})")
        if limit and total > limit:
            print(f"  (limited to {limit} this run)")

    # Lazy model load — sentence-transformers тяжёлый, инициируем только
    # когда работа реально есть.
    print("Loading model...")
    t0 = time.monotonic()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_ID, device="cpu")
    probe = model.encode(["probe"], normalize_embeddings=True)
    dim = int(probe.shape[-1])
    print(f"Loaded (dim={dim}) in {time.monotonic()-t0:.1f}s")

    import numpy as np

    processed = 0
    started = time.monotonic()
    iters = 0

    async with async_session() as db:
        while True:
            iters += 1
            # Берём батч pending секций.
            rows = (await db.execute(text("""
                SELECT
                    m.section_id, m.content_hash,
                    s.reglament_id, s.section_title, s.content
                FROM reglament_index_meta m
                JOIN reglament_sections s ON s.id = m.section_id
                LEFT JOIN reglament_embeddings e ON e.section_id = m.section_id
                WHERE e.section_id IS NULL
                   OR e.content_hash != m.content_hash
                   OR e.model_name != :model
                LIMIT :lim
            """), {"model": MODEL_ID, "lim": batch_size})).all()
            if not rows:
                break

            texts = []
            keys = []
            for sid, ch, rid, st, ct in rows:
                full = f"{st or ''}. {ct or ''}".strip()
                if not full:
                    continue
                texts.append(full)
                keys.append((sid, rid, ch))
            if not texts:
                break

            embeds = model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False, batch_size=16
            )

            for (sid, rid, ch), vec in zip(keys, embeds):
                blob = vec.astype(np.float32, copy=False).tobytes(order="C")
                await db.execute(text("""
                    INSERT INTO reglament_embeddings
                        (section_id, reglament_id, model_name, dim, embedding, content_hash, updated_at)
                    VALUES (:sid, :rid, :mn, :dim, :emb, :hash, CURRENT_TIMESTAMP)
                    ON CONFLICT(section_id) DO UPDATE SET
                        reglament_id = excluded.reglament_id,
                        model_name = excluded.model_name,
                        dim = excluded.dim,
                        embedding = excluded.embedding,
                        content_hash = excluded.content_hash,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    "sid": sid, "rid": rid, "mn": MODEL_ID, "dim": int(vec.shape[-1]),
                    "emb": blob, "hash": ch,
                })

            await db.commit()
            processed += len(texts)
            elapsed = time.monotonic() - started
            rate = processed / max(elapsed, 0.001)
            print(f"  iter#{iters}: +{len(texts)} = {processed}/{total} ({rate:.1f}/s)")
            if limit and processed >= limit:
                print(f"  reached limit {limit}, stopping early")
                break

    elapsed = time.monotonic() - started
    print(f"\n=== DONE in {elapsed:.1f}s ===")
    print(f"Embedded: {processed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap reglament_embeddings")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    try:
        asyncio.run(bootstrap(args.batch, args.limit))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
