"""
Bounded concurrency for file-upload handlers.

The executor panel can spike to 50-60 concurrent users; a burst of
simultaneous uploads would otherwise stampede SQLite writes (and large
in-memory file reads). This gates the upload handlers through a small
semaphore so excess requests queue and run a few at a time instead of
all at once. Synchronous request/response contract is unchanged — the
caller just waits its turn.

Tune via settings.UPLOAD_MAX_CONCURRENCY (<= 0 disables the limiter).
"""
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings

_limit = int(getattr(settings, "UPLOAD_MAX_CONCURRENCY", 0) or 0)
_semaphore = asyncio.Semaphore(_limit) if _limit > 0 else None


@asynccontextmanager
async def upload_slot():
    """Acquire one upload slot for the duration of the block. No-op when
    the limiter is disabled."""
    if _semaphore is None:
        yield
        return
    async with _semaphore:
        yield
