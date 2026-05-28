import logging
import time
from typing import Dict, Optional

try:
    import redis.asyncio as redis_asyncio
except Exception:  # pragma: no cover - optional dependency for local/dev bootstrapping
    redis_asyncio = None

from app.core.config import settings

logger = logging.getLogger(__name__)

_memory_login_attempts: Dict[str, Dict[str, float]] = {}
_memory_two_factor_challenges: Dict[str, Dict[str, float]] = {}
_memory_token_blacklist: Dict[str, float] = {}
_memory_user_revocations: Dict[str, float] = {}
_memory_api_rate_limits: Dict[str, Dict[str, float]] = {}
_redis_client = None
_redis_warned = False


async def _get_redis():
    global _redis_client, _redis_warned
    if not settings.REDIS_URL or redis_asyncio is None:
        return None
    if _redis_client is None:
        _redis_client = redis_asyncio.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await _redis_client.ping()
        return _redis_client
    except Exception as exc:  # pragma: no cover - runtime fallback
        if not _redis_warned:
            logger.warning("Redis is unavailable for auth security store, falling back to memory: %s", exc)
            _redis_warned = True
        return None


def _cleanup_memory_login_attempts() -> None:
    now = time.time()
    expired = [
        key
        for key, state in _memory_login_attempts.items()
        if state.get("expires_at", 0) <= now and state.get("attempts", 0) <= 0
    ]
    for key in expired:
        _memory_login_attempts.pop(key, None)


async def login_rate_limit_retry_after(key: str) -> Optional[int]:
    client = await _get_redis()
    if client is not None:
        ttl = await client.ttl(f"{settings.SECURITY_REDIS_PREFIX}:login:block:{key}")
        return int(ttl) if ttl and ttl > 0 else None

    _cleanup_memory_login_attempts()
    state = _memory_login_attempts.get(key)
    if not state:
        return None
    now = time.time()
    blocked_until = state.get("blocked_until", 0)
    if blocked_until > now:
        return int(max(1, blocked_until - now))
    if state.get("expires_at", 0) <= now:
        _memory_login_attempts.pop(key, None)
    return None


async def mark_login_failure(key: str, attempts_limit: int, window_seconds: int) -> None:
    client = await _get_redis()
    if client is not None:
        counter_key = f"{settings.SECURITY_REDIS_PREFIX}:login:attempts:{key}"
        block_key = f"{settings.SECURITY_REDIS_PREFIX}:login:block:{key}"
        attempts = await client.incr(counter_key)
        if attempts == 1:
            await client.expire(counter_key, window_seconds)
        if attempts >= attempts_limit:
            await client.set(block_key, "1", ex=window_seconds)
        return

    now = time.time()
    state = _memory_login_attempts.get(key)
    if not state or state.get("expires_at", 0) <= now:
        state = {"attempts": 0, "expires_at": now + window_seconds, "blocked_until": 0}
        _memory_login_attempts[key] = state
    state["attempts"] = state.get("attempts", 0) + 1
    if state["attempts"] >= attempts_limit:
        state["blocked_until"] = now + window_seconds


async def clear_login_failures(key: str) -> None:
    client = await _get_redis()
    if client is not None:
        await client.delete(
            f"{settings.SECURITY_REDIS_PREFIX}:login:attempts:{key}",
            f"{settings.SECURITY_REDIS_PREFIX}:login:block:{key}",
        )
        return
    _memory_login_attempts.pop(key, None)


def _cleanup_memory_challenges() -> None:
    now = time.time()
    expired = [
        challenge_id
        for challenge_id, state in _memory_two_factor_challenges.items()
        if state.get("expires_at", 0) <= now
    ]
    for challenge_id in expired:
        _memory_two_factor_challenges.pop(challenge_id, None)


async def register_two_factor_challenge(challenge_id: str, ttl_seconds: int) -> None:
    client = await _get_redis()
    if client is not None:
        await client.hset(
            f"{settings.SECURITY_REDIS_PREFIX}:2fa:challenge:{challenge_id}",
            mapping={"attempts": 0},
        )
        await client.expire(f"{settings.SECURITY_REDIS_PREFIX}:2fa:challenge:{challenge_id}", ttl_seconds)
        return
    _cleanup_memory_challenges()
    _memory_two_factor_challenges[challenge_id] = {
        "attempts": 0,
        "expires_at": time.time() + ttl_seconds,
    }


async def get_two_factor_challenge_state(challenge_id: str) -> Optional[Dict[str, float]]:
    client = await _get_redis()
    if client is not None:
        key = f"{settings.SECURITY_REDIS_PREFIX}:2fa:challenge:{challenge_id}"
        values = await client.hgetall(key)
        if not values:
            return None
        ttl = await client.ttl(key)
        return {
            "attempts": float(values.get("attempts", 0) or 0),
            "expires_at": time.time() + max(ttl, 0),
        }
    _cleanup_memory_challenges()
    return _memory_two_factor_challenges.get(challenge_id)


async def mark_two_factor_challenge_failure(challenge_id: str) -> None:
    client = await _get_redis()
    if client is not None:
        await client.hincrby(f"{settings.SECURITY_REDIS_PREFIX}:2fa:challenge:{challenge_id}", "attempts", 1)
        return
    state = _memory_two_factor_challenges.get(challenge_id)
    if not state:
        return
    state["attempts"] = state.get("attempts", 0) + 1


async def clear_two_factor_challenge(challenge_id: str) -> None:
    client = await _get_redis()
    if client is not None:
        await client.delete(f"{settings.SECURITY_REDIS_PREFIX}:2fa:challenge:{challenge_id}")
        return
    _memory_two_factor_challenges.pop(challenge_id, None)


def _cleanup_memory_token_blacklist() -> None:
    now = time.time()
    expired = [jti for jti, expires_at in _memory_token_blacklist.items() if expires_at <= now]
    for jti in expired:
        _memory_token_blacklist.pop(jti, None)


async def blacklist_token_jti(jti: str, expires_at_ts: int) -> None:
    if not jti:
        return
    ttl = int(expires_at_ts - time.time())
    if ttl <= 0:
        return
    client = await _get_redis()
    if client is not None:
        await client.set(f"{settings.SECURITY_REDIS_PREFIX}:token:blacklist:{jti}", "1", ex=ttl)
        return
    _cleanup_memory_token_blacklist()
    _memory_token_blacklist[jti] = time.time() + ttl


async def is_token_blacklisted(jti: Optional[str]) -> bool:
    if not jti:
        return False
    client = await _get_redis()
    if client is not None:
        return bool(await client.exists(f"{settings.SECURITY_REDIS_PREFIX}:token:blacklist:{jti}"))
    _cleanup_memory_token_blacklist()
    return jti in _memory_token_blacklist


async def revoke_user_tokens(user_id: str, revoked_after_ts: Optional[int] = None) -> int:
    if not user_id:
        return 0
    issued_after = int(revoked_after_ts or time.time())
    ttl = (settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60) + 3600
    client = await _get_redis()
    if client is not None:
        key = f"{settings.SECURITY_REDIS_PREFIX}:user:revoked-after:{user_id}"
        existing = await client.get(key)
        if existing is not None:
            try:
                issued_after = max(issued_after, int(existing))
            except (TypeError, ValueError):
                pass
        await client.set(key, str(issued_after), ex=ttl)
        return issued_after

    existing = int(_memory_user_revocations.get(user_id, 0) or 0)
    issued_after = max(issued_after, existing)
    _memory_user_revocations[user_id] = issued_after
    return issued_after


async def get_user_revoked_after(user_id: Optional[str]) -> Optional[int]:
    if not user_id:
        return None
    client = await _get_redis()
    if client is not None:
        value = await client.get(f"{settings.SECURITY_REDIS_PREFIX}:user:revoked-after:{user_id}")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    value = _memory_user_revocations.get(user_id)
    return int(value) if value else None


def _cleanup_memory_api_rate_limits() -> None:
    now = time.time()
    expired = [
        key
        for key, state in _memory_api_rate_limits.items()
        if state.get("expires_at", 0) <= now
    ]
    for key in expired:
        _memory_api_rate_limits.pop(key, None)


async def consume_rate_limit(bucket: str, key: str, limit: int, window_seconds: int) -> Optional[int]:
    if not bucket or not key or limit <= 0 or window_seconds <= 0:
        return None
    client = await _get_redis()
    if client is not None:
        counter_key = f"{settings.SECURITY_REDIS_PREFIX}:ratelimit:{bucket}:{key}"
        current = await client.incr(counter_key)
        if current == 1:
            await client.expire(counter_key, window_seconds)
        if current > limit:
            ttl = await client.ttl(counter_key)
            return int(ttl) if ttl and ttl > 0 else window_seconds
        return None

    _cleanup_memory_api_rate_limits()
    now = time.time()
    memory_key = f"{bucket}:{key}"
    state = _memory_api_rate_limits.get(memory_key)
    if not state or state.get("expires_at", 0) <= now:
        state = {"count": 0, "expires_at": now + window_seconds}
        _memory_api_rate_limits[memory_key] = state
    state["count"] = state.get("count", 0) + 1
    if state["count"] > limit:
        return int(max(1, state["expires_at"] - now))
    return None
