"""
Yandex OAuth helpers for mail access.
"""
import base64
import hashlib
import hmac
import time
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings


AUTH_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"


def _sign_state(payload: str) -> str:
    secret = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def build_state(mailbox_id: str, user_id: str, ttl_seconds: int = 600) -> str:
    ts = int(time.time())
    payload = f"{mailbox_id}:{user_id}:{ts}:{ttl_seconds}"
    sig = _sign_state(payload)
    raw = f"{payload}:{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def verify_state(state: str) -> Optional[Dict[str, str]]:
    if not state:
        return None
    padded = state + "=" * (-len(state) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
    except Exception:
        return None
    parts = raw.split(":")
    if len(parts) < 5:
        return None
    mailbox_id, user_id, ts_str, ttl_str = parts[0], parts[1], parts[2], parts[3]
    sig = parts[4]
    payload = f"{mailbox_id}:{user_id}:{ts_str}:{ttl_str}"
    if not hmac.compare_digest(sig, _sign_state(payload)):
        return None
    try:
        ts = int(ts_str)
        ttl = int(ttl_str)
    except ValueError:
        return None
    if int(time.time()) > ts + ttl:
        return None
    return {"mailbox_id": mailbox_id, "user_id": user_id}


def build_auth_url(state: str, login_hint: Optional[str] = None) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.YANDEX_OAUTH_CLIENT_ID,
        "redirect_uri": settings.YANDEX_OAUTH_REDIRECT_URI,
        "scope": settings.YANDEX_OAUTH_SCOPES,
        "state": state,
        "force_confirm": "yes",
        "prompt": "login",
    }
    if login_hint:
        params["login_hint"] = login_hint
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> Dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.YANDEX_OAUTH_CLIENT_ID,
        "client_secret": settings.YANDEX_OAUTH_CLIENT_SECRET,
        "redirect_uri": settings.YANDEX_OAUTH_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()


async def refresh_token(refresh_token: str) -> Dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.YANDEX_OAUTH_CLIENT_ID,
        "client_secret": settings.YANDEX_OAUTH_CLIENT_SECRET,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()
