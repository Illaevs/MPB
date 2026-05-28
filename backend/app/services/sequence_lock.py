"""
In-process serialization for racy MAX(number)+1 allocations.

Several create paths assign a human/sequence number as
`SELECT MAX(col)+1` then INSERT. Under concurrency two requests read the
same max and produce a duplicate (silent dup where there is no UNIQUE
constraint — kp / contract docs / version numbers — or a 500 where
there is). The deployment is single-process (SQLite; the in-memory
rate-limiter / security store already assume one worker), so an
in-process async lock around "read max -> insert -> commit" fully
closes the race with no schema change. It is intentionally NOT
multi-process — SQLite write scaling is single-process anyway.

Lock names group by sequence so unrelated allocations don't block each
other. Hold the lock only across the allocation + its commit; these are
low-frequency document/KP/version creations, not hot paths.
"""
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager

_locks: "defaultdict[str, asyncio.Lock]" = defaultdict(asyncio.Lock)


@asynccontextmanager
async def sequence_lock(name: str):
    """Serialize the wrapped number-allocation region by `name`."""
    async with _locks[name]:
        yield
