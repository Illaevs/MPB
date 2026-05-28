"""
AI service helpers for Ollama-backed assistant features.
"""
from __future__ import annotations

import json
import re
from html import escape
from typing import Any, Iterable, Optional

import httpx

from app.core.config import settings


class AIServiceError(RuntimeError):
    """Raised when AI provider interaction fails."""


def ai_is_enabled() -> bool:
    return bool(settings.AI_ENABLED and settings.AI_OLLAMA_BASE_URL.strip())


def _normalize_base_url() -> str:
    return settings.AI_OLLAMA_BASE_URL.rstrip("/")


def _strip_code_fences(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json|html|text)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _coerce_html(value: Optional[str]) -> str:
    text = _strip_code_fences(value or "")
    if not text:
        return ""
    if re.search(r"<(?:p|div|ul|ol|li|strong|em|br)\b", text, flags=re.IGNORECASE):
        return text
    paragraphs = [segment.strip() for segment in re.split(r"\n{2,}", text) if segment.strip()]
    if not paragraphs:
        return ""
    return "".join(f"<p>{escape(segment).replace(chr(10), '<br>')}</p>" for segment in paragraphs)


def _plain_text_from_html(value: Optional[str]) -> str:
    html = str(value or "")
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_json_payload(value: str) -> dict[str, Any]:
    text = _strip_code_fences(value)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


async def ollama_tags() -> dict[str, Any]:
    if not ai_is_enabled():
        return {"models": []}
    url = f"{_normalize_base_url()}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=min(settings.AI_TIMEOUT_SECONDS, 10), verify=settings.AI_VERIFY_SSL) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AIServiceError(f"Ollama status request failed: {exc}") from exc
    return response.json()


async def ollama_chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    if not ai_is_enabled():
        raise AIServiceError("AI assistant is disabled")

    payload = {
        "model": model or settings.AI_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": temperature,
        },
    }
    url = f"{_normalize_base_url()}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS, verify=settings.AI_VERIFY_SSL) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AIServiceError(f"Ollama request failed: {exc}") from exc

    raw_payload = response.json()
    content = (
        raw_payload.get("message", {}).get("content")
        if isinstance(raw_payload, dict)
        else ""
    )
    parsed = _extract_json_payload(content)
    answer_value = str(parsed.get("answer") or "").strip()
    html_value = _coerce_html(parsed.get("html") or parsed.get("content") or parsed.get("text") or answer_value)
    text_value = str(parsed.get("text") or answer_value or _plain_text_from_html(html_value) or "").strip()
    used_fields = parsed.get("used_fields") or []
    warnings = parsed.get("warnings") or []
    summary = parsed.get("summary")
    return {
        "model": str(raw_payload.get("model") or payload["model"]),
        "answer": answer_value,
        "html": html_value,
        "text": text_value,
        "used_fields": [str(item) for item in used_fields if str(item).strip()],
        "warnings": [str(item) for item in warnings if str(item).strip()],
        "summary": str(summary).strip() if summary else None,
        "parsed": parsed,
        "raw": raw_payload,
    }


def compact_scalar_mapping(mapping: dict[str, Any], *, limit: int = 60) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in mapping.items():
        if len(compact) >= limit:
            break
        if isinstance(value, (dict, list, tuple, set)):
            continue
        if value in (None, ""):
            continue
        compact[str(key)] = value
    return compact


def list_preview(items: Iterable[dict[str, Any]], keys: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if index >= limit:
            break
        if not isinstance(item, dict):
            continue
        preview.append({key: item.get(key) for key in keys if item.get(key) not in (None, "")})
    return preview
