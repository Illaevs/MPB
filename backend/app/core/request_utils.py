"""Request helpers shared by middleware and routers."""
from fastapi import Request

from app.core.config import settings


def client_ip(request: Request) -> str:
    """Resolve the real client IP without trusting a client-supplied
    X-Forwarded-For prefix.

    Behind ``TRUSTED_PROXY_HOPS`` reverse proxies the genuine client IP is the
    entry that the nearest trusted proxy appended, i.e. the Nth value counting
    from the right of X-Forwarded-For. Anything the client itself injected ends
    up to the left of that and is ignored. ``TRUSTED_PROXY_HOPS == 0`` ignores
    the header entirely and uses the raw socket peer.
    """
    hops = int(getattr(settings, "TRUSTED_PROXY_HOPS", 1) or 0)
    if hops > 0:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if parts:
                idx = len(parts) - hops
                if idx < 0:
                    idx = 0
                return parts[idx] or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
