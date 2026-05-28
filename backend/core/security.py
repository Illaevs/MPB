"""
Security helpers: password hashing and JWT tokens.
"""
import base64
import binascii
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


class TokenDecodeError(ValueError):
    """Raised when a JWT cannot be decoded or validated."""


class TokenExpiredError(TokenDecodeError):
    """Raised when a JWT has expired."""

_PBKDF2_PREFIX = "pbkdf2_sha256"
_PBKDF2_LEGACY_PREFIX = "$pbkdf2-sha256$"
_PBKDF2_DEFAULT_ROUNDS = 390_000
_PBKDF2_SALT_BYTES = 16


def _urlsafe_b64encode_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _urlsafe_b64decode_no_pad(value: str) -> bytes:
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _passlib_b64decode(value: str) -> bytes:
    padded = value.replace(".", "+") + ("=" * ((4 - len(value) % 4) % 4))
    return base64.b64decode(padded.encode("ascii"))


def _pbkdf2_digest(password: str, salt: bytes, rounds: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)


def _verify_custom_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        _, rounds_raw, salt_raw, digest_raw = hashed_password.split("$", 3)
        rounds = int(rounds_raw)
        salt = _urlsafe_b64decode_no_pad(salt_raw)
        expected = _urlsafe_b64decode_no_pad(digest_raw)
    except (ValueError, TypeError, binascii.Error):
        return False
    actual = _pbkdf2_digest(plain_password, salt, rounds)
    return hmac.compare_digest(actual, expected)


def _verify_legacy_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        _, _, rounds_raw, salt_raw, digest_raw = hashed_password.split("$", 4)
        rounds = int(rounds_raw)
        salt = _passlib_b64decode(salt_raw)
        expected = _passlib_b64decode(digest_raw)
    except (ValueError, TypeError, binascii.Error):
        return False
    actual = _pbkdf2_digest(plain_password, salt, rounds)
    return hmac.compare_digest(actual, expected)


def _verify_bcrypt(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    if hashed_password.startswith(f"{_PBKDF2_PREFIX}$"):
        return _verify_custom_pbkdf2(plain_password, hashed_password)
    if hashed_password.startswith(_PBKDF2_LEGACY_PREFIX):
        return _verify_legacy_pbkdf2(plain_password, hashed_password)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        return _verify_bcrypt(plain_password, hashed_password)
    return False


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_PBKDF2_SALT_BYTES)
    digest = _pbkdf2_digest(password, salt, _PBKDF2_DEFAULT_ROUNDS)
    return f"{_PBKDF2_PREFIX}${_PBKDF2_DEFAULT_ROUNDS}${_urlsafe_b64encode_no_pad(salt)}${_urlsafe_b64encode_no_pad(digest)}"


def _build_exp(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def create_token(data: Dict[str, Any], expires_minutes: int, token_type: str) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "iat": now,
            "exp": _build_exp(expires_minutes),
            "type": token_type,
            "jti": uuid.uuid4().hex,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: Dict[str, Any]) -> str:
    return create_token(data, settings.ACCESS_TOKEN_EXPIRE_MINUTES, token_type="access")


def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_token(data, settings.REFRESH_TOKEN_EXPIRE_MINUTES, token_type="refresh")


def create_two_factor_challenge_token(data: Dict[str, Any]) -> str:
    return create_token(data, settings.TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES, token_type="2fa_challenge")


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Token expired") from exc
    except InvalidTokenError as exc:
        raise TokenDecodeError("Invalid token") from exc


def is_token_type(payload: Dict[str, Any], expected: str) -> bool:
    return payload.get("type") == expected


def token_timestamp(payload: Dict[str, Any], field: str) -> Optional[int]:
    value = payload.get(field)
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
