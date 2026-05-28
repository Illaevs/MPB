"""
Helpers for TOTP-based two-factor authentication.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from typing import List, Optional, Tuple
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.security import hash_password, verify_password


TOTP_DIGITS = 6
TOTP_INTERVAL_SECONDS = 30
TOTP_SECRET_BYTES = 20
BACKUP_CODES_COUNT = 8


def _build_fernet() -> Fernet:
    digest = hashlib.sha256(f"{settings.SECRET_KEY}|two-factor".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _normalize_base32_secret(secret: str) -> str:
    return "".join(ch for ch in str(secret or "").upper() if ch.isalnum())


def _decode_base32_secret(secret: str) -> bytes:
    normalized = _normalize_base32_secret(secret)
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized + padding, casefold=True)


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(TOTP_SECRET_BYTES)).decode("ascii").rstrip("=")


def encrypt_totp_secret(secret: str) -> str:
    normalized = _normalize_base32_secret(secret)
    return _build_fernet().encrypt(normalized.encode("utf-8")).decode("utf-8")


def decrypt_totp_secret(secret_enc: Optional[str]) -> Optional[str]:
    if not secret_enc:
        return None
    try:
        return _build_fernet().decrypt(secret_enc.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def build_otpauth_uri(secret: str, email: str, issuer: Optional[str] = None) -> str:
    issuer_value = issuer or settings.TWO_FACTOR_ISSUER
    label = quote(f"{issuer_value}:{email}")
    issuer_qs = quote(issuer_value)
    return (
        f"otpauth://totp/{label}"
        f"?secret={_normalize_base32_secret(secret)}"
        f"&issuer={issuer_qs}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_INTERVAL_SECONDS}"
    )


def _generate_totp_code(secret: str, at_time: Optional[int] = None) -> str:
    key = _decode_base32_secret(secret)
    ts = int(at_time or time.time())
    counter = ts // TOTP_INTERVAL_SECONDS
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return str(code_int % (10 ** TOTP_DIGITS)).zfill(TOTP_DIGITS)


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    normalized_code = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(normalized_code) != TOTP_DIGITS:
        return False
    now = int(time.time())
    for offset in range(-window, window + 1):
        candidate = _generate_totp_code(secret, now + (offset * TOTP_INTERVAL_SECONDS))
        if hmac.compare_digest(candidate, normalized_code):
            return True
    return False


def _normalize_backup_code(code: str) -> str:
    return "".join(ch for ch in str(code or "").upper() if ch.isalnum())


def generate_backup_codes(count: int = BACKUP_CODES_COUNT) -> List[str]:
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(4).upper()
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_backup_codes(codes: List[str]) -> str:
    normalized = [_normalize_backup_code(code) for code in codes if _normalize_backup_code(code)]
    return json.dumps([hash_password(code) for code in normalized], ensure_ascii=False)


def parse_backup_code_hashes(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except Exception:
        return []
    return [str(item) for item in value if item]


def count_backup_codes(raw: Optional[str]) -> int:
    return len(parse_backup_code_hashes(raw))


def verify_and_consume_backup_code(code: str, raw_hashes: Optional[str]) -> Tuple[bool, str]:
    normalized = _normalize_backup_code(code)
    hashes = parse_backup_code_hashes(raw_hashes)
    if not normalized or not hashes:
        return False, json.dumps(hashes, ensure_ascii=False)

    for idx, hashed in enumerate(hashes):
        try:
            if verify_password(normalized, hashed):
                updated = hashes[:idx] + hashes[idx + 1 :]
                return True, json.dumps(updated, ensure_ascii=False)
        except Exception:
            continue
    return False, json.dumps(hashes, ensure_ascii=False)
