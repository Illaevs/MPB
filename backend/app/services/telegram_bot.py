"""
Telegram Bot API helpers.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Optional, Sequence

import httpx

from app.core.config import settings


def telegram_bot_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_USERNAME)


def build_telegram_deep_link(token: str) -> Optional[str]:
    if not settings.TELEGRAM_BOT_USERNAME or not token:
        return None
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"


def build_external_action_url(action_url: Optional[str]) -> Optional[str]:
    if not action_url:
        return None
    if action_url.startswith("http://") or action_url.startswith("https://"):
        return action_url
    base_url = (settings.PUBLIC_APP_URL or "").rstrip("/")
    if not base_url:
        return action_url
    normalized_path = action_url if action_url.startswith("/") else f"/{action_url}"
    return f"{base_url}{normalized_path}"


def build_telegram_message(
    title: str,
    message: Optional[str] = None,
    action_url: Optional[str] = None,
) -> str:
    parts = [f"<b>{escape(title or 'Уведомление')}</b>"]
    if message:
        parts.append(escape(message))
    external_action_url = build_external_action_url(action_url)
    if external_action_url:
        parts.append(f'<a href="{escape(external_action_url, quote=True)}">Открыть в системе</a>')
    return "\n\n".join(part for part in parts if part).strip()


async def send_telegram_message(
    chat_id: str,
    text: str,
    *,
    disable_web_page_preview: bool = True,
    reply_markup: Optional[dict] = None,
) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram bot token is not configured")
    if not chat_id:
        raise RuntimeError("Telegram chat_id is empty")

    api_base_url = (settings.TELEGRAM_API_BASE_URL or "https://api.telegram.org").rstrip("/")
    url = f"{api_base_url}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    timeout = httpx.Timeout(settings.TELEGRAM_API_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json() or {}
        if not data.get("ok"):
            raise RuntimeError(data.get("description") or "Telegram API request failed")
        return data.get("result") or {}


async def send_telegram_document(
    chat_id: str,
    document: bytes,
    filename: str,
    *,
    caption: Optional[str] = None,
) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram bot token is not configured")
    if not chat_id:
        raise RuntimeError("Telegram chat_id is empty")
    if not document:
        raise RuntimeError("Telegram document is empty")

    api_base_url = (settings.TELEGRAM_API_BASE_URL or "https://api.telegram.org").rstrip("/")
    url = f"{api_base_url}/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    timeout = httpx.Timeout(settings.TELEGRAM_API_TIMEOUT_SECONDS)
    data = {"chat_id": str(chat_id)}
    if caption:
        data["caption"] = caption
        data["parse_mode"] = "HTML"

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url,
            data=data,
            files={"document": (filename or "report.pdf", document, "application/pdf")},
        )
        response.raise_for_status()
        payload = response.json() or {}
        if not payload.get("ok"):
            raise RuntimeError(payload.get("description") or "Telegram API request failed")
        return payload.get("result") or {}


async def answer_telegram_callback_query(
    callback_query_id: str,
    *,
    text: Optional[str] = None,
    show_alert: bool = False,
) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram bot token is not configured")
    if not callback_query_id:
        raise RuntimeError("Telegram callback_query_id is empty")

    api_base_url = (settings.TELEGRAM_API_BASE_URL or "https://api.telegram.org").rstrip("/")
    url = f"{api_base_url}/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = {
        "callback_query_id": str(callback_query_id),
        "show_alert": bool(show_alert),
    }
    if text:
        payload["text"] = text
    timeout = httpx.Timeout(settings.TELEGRAM_API_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json() or {}
        if not data.get("ok"):
            raise RuntimeError(data.get("description") or "Telegram API request failed")
        return data.get("result") or {}


async def set_telegram_bot_commands(commands: Sequence[dict[str, str]]) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram bot token is not configured")

    api_base_url = (settings.TELEGRAM_API_BASE_URL or "https://api.telegram.org").rstrip("/")
    url = f"{api_base_url}/bot{settings.TELEGRAM_BOT_TOKEN}/setMyCommands"
    timeout = httpx.Timeout(settings.TELEGRAM_API_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json={"commands": list(commands or [])})
        response.raise_for_status()
        data = response.json() or {}
        if not data.get("ok"):
            raise RuntimeError(data.get("description") or "Telegram API request failed")
        return data.get("result") or {}


async def fetch_telegram_updates(
    *,
    offset: Optional[int] = None,
    timeout_seconds: int = 0,
    limit: int = 100,
) -> list[dict]:
    if not settings.TELEGRAM_BOT_TOKEN:
        return []

    api_base_url = (settings.TELEGRAM_API_BASE_URL or "https://api.telegram.org").rstrip("/")
    url = f"{api_base_url}/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
    timeout = httpx.Timeout(max(settings.TELEGRAM_API_TIMEOUT_SECONDS, timeout_seconds + 5))

    payload: dict[str, int] = {
        "timeout": max(0, int(timeout_seconds)),
        "limit": max(1, min(int(limit), 100)),
    }
    if offset is not None:
        payload["offset"] = int(offset)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json() or {}
        if not data.get("ok"):
            raise RuntimeError(data.get("description") or "Telegram API request failed")
        result = data.get("result") or []
        return result if isinstance(result, list) else []


def utcnow_naive() -> datetime:
    return datetime.utcnow()
