"""
IMAP helpers for Yandex Mail via OAuth2.
"""
import base64
import codecs
import email
import html
import imaplib
import quopri
import re
import socket
import unicodedata
from datetime import datetime
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import PurePath
from typing import List, Dict, Optional
from urllib.parse import urlparse, unquote


IMAP_HOST = "imap.yandex.ru"
IMAP_PORT = 993
MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
ALLOWED_EXTERNAL_ATTACHMENT_HOST_SUFFIXES = (
    "disk.yandex.ru",
    "yadi.sk",
    "downloader.disk.yandex.ru",
    "cloud.mail.ru",
    "drive.google.com",
    "docs.google.com",
    "dropbox.com",
    "onedrive.live.com",
    "sharepoint.com",
)
FILE_LINK_HINT_RE = re.compile(
    r"(\u0441\u043a\u0430\u0447|\u0430\u0440\u0445\u0438\u0432|\u0432\u043b\u043e\u0436\u0435\u043d|\u0444\u0430\u0439\u043b|download|attachment|archive|\.zip|\.rar|\.7z|\.pdf|\.docx?|\.xlsx?)",
    re.I,
)
BLOCKED_ATTACHMENT_EXTENSIONS = {
    ".ade",
    ".adp",
    ".apk",
    ".app",
    ".bat",
    ".cmd",
    ".com",
    ".cpl",
    ".dll",
    ".exe",
    ".gadget",
    ".hta",
    ".htm",
    ".html",
    ".ins",
    ".iso",
    ".isp",
    ".jar",
    ".js",
    ".jse",
    ".lnk",
    ".msi",
    ".msp",
    ".pif",
    ".ps1",
    ".scr",
    ".sh",
    ".svg",
    ".vb",
    ".vbe",
    ".vbs",
    ".ws",
    ".wsc",
    ".wsf",
}


def _is_common_letter(ch: str) -> bool:
    code = ord(ch)
    if 0x41 <= code <= 0x5A or 0x61 <= code <= 0x7A:
        return True
    if 0x0400 <= code <= 0x052F or ch in ("Ё", "ё"):
        return True
    return False


def _text_score(text: str) -> float:
    if not text:
        return 0.0
    length = max(len(text), 1)
    spaces = sum(1 for ch in text if ch.isspace())
    digits = sum(1 for ch in text if ch.isdigit())
    common_letters = sum(1 for ch in text if _is_common_letter(ch))
    vowels = set("aeiouyAEIOUYаеёиоуыэюяАЕЁИОУЫЭЮЯ")
    vowel_count = sum(1 for ch in text if ch in vowels)
    letters = sum(1 for ch in text if ch.isalpha())
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\r\n\t")
    replacement = text.count("\ufffd")
    # Count high latin1 chars (0x80-0xFF range, non-Cyrillic) — these indicate wrong encoding
    high_latin1 = sum(1 for ch in text if 0x80 <= ord(ch) <= 0xFF)
    base = (common_letters * 2 + digits + spaces) / length + printable / length
    # Penalize replacement chars and suspicious high latin1 bytes
    if replacement > 0:
        base -= (replacement / length) * 4.0
    if high_latin1 > 0 and common_letters < high_latin1:
        # Lots of high bytes but few recognized letters → likely wrong encoding
        base -= (high_latin1 / length) * 1.5
    if letters > 20 and vowel_count / max(letters, 1) < 0.2:
        # Text with letters but almost no vowels is likely garbled
        base -= 0.6
    return base


def _looks_gibberish(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if re.search(r"</?(html|body|head|div|p|table|br|span|ul|ol|li|blockquote)\b", text, re.I):
        return False
    length = len(stripped)
    if length < 16:
        return False
    spaces = sum(1 for ch in stripped if ch.isspace())
    digits = sum(1 for ch in stripped if ch.isdigit())
    letters = sum(1 for ch in stripped if ch.isalpha())
    common_letters = sum(1 for ch in stripped if _is_common_letter(ch))
    control_chars = sum(
        1
        for ch in stripped
        if unicodedata.category(ch) == "Cc" and ch not in ("\r", "\n", "\t")
    )
    if control_chars / max(length, 1) > 0.01:
        return True

    allowed = 0
    for ch in stripped:
        if ch.isspace() or ch.isalnum():
            allowed += 1
            continue
        if ch in ".,;:!?\"'()[]{}<>@#$%^&*-_=+/\\|`~—–«»№…":
            allowed += 1
            continue
        if unicodedata.category(ch).startswith("P"):
            allowed += 1
    allowed_ratio = allowed / max(length, 1)
    if length > 80 and allowed_ratio < 0.65:
        return True
    if length > 40 and allowed_ratio < 0.55:
        return True
    tokens = re.split(r"\s+", stripped)
    max_token = max((len(t) for t in tokens if t), default=0)
    if length > 80 and max_token / max(length, 1) > 0.8:
        return True
    if max_token > 120 and spaces < 4:
        return True
    vowels = set("aeiouyAEIOUYаеёиоуыэюяАЕЁИОУЫЭЮЯ")
    vowel_count = sum(1 for ch in stripped if ch in vowels)
    if spaces <= 1 and length > 40:
        if (common_letters + digits) / length < 0.4:
            return True
        if letters and common_letters / max(letters, 1) < 0.6:
            return True
        if common_letters > 20 and vowel_count / max(common_letters, 1) < 0.2:
            return True
    return False


def _fix_7bit_stripped_cp1251(text: str) -> str:
    """
    Fix text where CP1251 Cyrillic bytes had 0xB0 subtracted during transit.
    Each CP1251 byte B became (B - 0xB0), so:
      lowercase а-п (0xE0-0xEF) → 0x30-0x3F (digits/symbols like 0-9:;<=>?)
      lowercase р-я (0xF0-0xFF) → 0x40-0x4F (@A-O)
      uppercase Р-Я (0xD0-0xDF) → 0x20-0x2F (space/punctuation, ambiguous)
      uppercase А-П (0xC0-0xCF) → 0x10-0x1F (control chars, LOST)
    Recovery: add 0xB0 to chars in 0x21-0x4F range, decode as CP1251.
    Chars 0x50-0x7E (P-~) are NOT shifted — they don't occur in this corruption
    (they'd correspond to bytes 0x100+ which don't exist in CP1251).
    """
    if not text or len(text) < 8:
        return text
    # Quick check: if already has enough Cyrillic, skip
    cyr_count = sum(1 for ch in text if _is_common_letter(ch) and ord(ch) >= 0x400)
    if cyr_count / max(len(text), 1) > 0.1:
        return text
    # Count chars in the "shifted Cyrillic" range 0x30-0x4F
    potential = sum(1 for ch in text if 0x30 <= ord(ch) <= 0x4F)
    spaces = sum(1 for ch in text if ch.isspace())
    total = len(text) - spaces
    if potential < 8 or total <= 0 or potential / total < 0.4:
        return text
    # Check for suspicious sequences (consecutive shifted chars)
    suspicious = re.findall(r'[0-9:;<=>?@A-O]{3,}', text)
    if len(suspicious) < 2:
        return text

    # Recover: shift 0x30-0x4F by +0xB0 (main Cyrillic range)
    # Also shift 0x21-0x2F by +0xB0 (uppercase Р-Я) with smart punctuation handling
    result = []
    chars = list(text)
    n = len(chars)
    for i, ch in enumerate(chars):
        code = ord(ch)
        nxt = ord(chars[i + 1]) if i < n - 1 else -1
        prev = ord(chars[i - 1]) if i > 0 else -1

        if 0x30 <= code <= 0x4F:
            # Main range: digits/symbols → lowercase а-я, @A-O → uppercase/lowercase
            # Check for Latin context: letter A-O next to P-Z or a-z means real Latin
            if 0x41 <= code <= 0x4F:
                # Could be Latin A-O or shifted Cyrillic
                # Latin if neighbor is clearly Latin (0x50-0x7A range, not shiftable)
                next_latin = (0x50 <= nxt <= 0x7A)
                prev_latin = (0x50 <= prev <= 0x7A)
                if next_latin or prev_latin:
                    result.append(code)  # keep as Latin
                    continue
            if code == 0x3F:  # ? — could be real '?' or 'п'
                at_end = nxt in (-1, 0x20, 0x0A, 0x0D)
                prev_is_shifted = 0x30 <= prev <= 0x4F
                prev2 = ord(chars[i - 2]) if i >= 2 else -1
                long_word = prev_is_shifted and (0x30 <= prev2 <= 0x4F)
                if at_end and long_word:
                    result.append(code)  # keep as '?'
                    continue
            result.append(code + 0xB0)
        elif code == 0x20:
            # Space stays space (could be shifted Р=0xD0, but indistinguishable)
            result.append(code)
        elif 0x21 <= code <= 0x2F:
            # Ambiguous range: punctuation vs uppercase Р-Я
            # Use context: if surrounded by shifted chars, it's likely Cyrillic
            p_shifted = 0x30 <= prev <= 0x4F
            n_shifted = 0x30 <= nxt <= 0x4F
            if code == 0x2C:  # ',' or 'Ь' (0xDC)
                # Comma is very common punctuation; Ь is rare between words
                # Keep as comma in most cases
                result.append(code)
            elif code == 0x2E:  # '.' or 'Ю' (0xDE)
                if nxt in (-1, 0x20, 0x0A, 0x0D):
                    result.append(code)  # likely real period
                elif p_shifted and n_shifted:
                    result.append(code + 0xB0)
                else:
                    result.append(code)
            elif code == 0x21:  # '!' or 'С' (0xD1)
                at_word_start = (prev in (0x20, 0x0A, 0x0D, -1)) and n_shifted
                if nxt in (-1, 0x20, 0x0A, 0x0D) and not at_word_start:
                    result.append(code)  # likely real '!'
                elif p_shifted or n_shifted or at_word_start:
                    result.append(code + 0xB0)
                else:
                    result.append(code)
            elif code == 0x2D:  # '-' or 'Э' (0xDD)
                if (prev == 0x20 or prev == -1) and (nxt == 0x20 or nxt == -1):
                    result.append(code)  # likely real dash
                elif p_shifted and n_shifted:
                    result.append(code + 0xB0)
                else:
                    result.append(code)
            else:
                # Other punct (!"#$%&'()*+/): shift if between shifted chars
                # or at start of a word (after space) followed by shifted char
                at_word_start = (prev in (0x20, 0x0A, 0x0D, -1)) and n_shifted
                if (p_shifted and n_shifted) or at_word_start:
                    result.append(code + 0xB0)
                else:
                    result.append(code)
        elif code < 0x20:
            # Control chars: could be shifted uppercase А-П (0xC0-0xCF → 0x10-0x1F)
            if 0x10 <= code <= 0x1F:
                result.append(code + 0xB0)  # recover А-П
            else:
                result.append(0x20)  # replace other control chars with space
        else:
            # 0x50-0x7E range or > 0xFF: keep as-is
            result.append(code if code <= 0xFF else 0x20)

    try:
        recovered = bytes(result).decode("cp1251", errors="replace")
        new_cyr = sum(1 for ch in recovered if _is_common_letter(ch) and ord(ch) >= 0x400)
        if new_cyr > cyr_count + 5:
            return recovered
    except Exception:
        pass
    return text


def _fix_7bit_stripped_cp1251_mask(text: str) -> str:
    """
    Fix text where 8th bit was stripped via & 0x7F (7-bit transport), so:
      CP1251 uppercase 0xC0-0xDF -> 0x40-0x5F (@ to _)
      CP1251 lowercase 0xE0-0xFF -> 0x60-0x7F (` to DEL)
    Recovery: add 0x80 to 0x40-0x7F bytes, decode as CP1251.
    Uses heuristics to avoid corrupting legitimate ASCII (URLs/emails).
    """
    if not text or len(text) < 8:
        return text
    cyr_count = sum(1 for ch in text if _is_common_letter(ch) and ord(ch) >= 0x400)
    if cyr_count / max(len(text), 1) > 0.1:
        return text
    ascii_hi = sum(1 for ch in text if 0x40 <= ord(ch) <= 0x7F)
    spaces = sum(1 for ch in text if ch.isspace())
    total = max(len(text) - spaces, 1)
    if ascii_hi < 8 or ascii_hi / total < 0.35:
        return text

    protected = [False] * len(text)
    for match in re.finditer(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", text):
        for i in range(match.start(), match.end()):
            protected[i] = True
    for match in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        for i in range(match.start(), match.end()):
            protected[i] = True

    result = []
    for i, ch in enumerate(text):
        code = ord(ch)
        if code > 0xFF:
            result.append(0x20)
            continue
        if protected[i]:
            result.append(code)
            continue
        if 0x40 <= code <= 0x7F:
            result.append(code + 0x80)
        else:
            result.append(code)

    try:
        recovered = bytes(result).decode("cp1251", errors="replace")
        if _text_score(recovered) > _text_score(text) + 0.2:
            return recovered
    except Exception:
        pass
    return text


def _fix_utf8_double_encoded_win1251(text: str) -> str:
    """
    Fix text where UTF-8 bytes were decoded as windows-1251, producing
    sequences like 'Р' (U+0420) + 'џ' (U+045F) for what should be 'П' (U+041F).
    Recovery: encode back to windows-1251 → decode as UTF-8.
    """
    if not text or len(text) < 6:
        return text
    # Quick check: UTF-8 lead bytes 0xD0/0xD1 become Р/С in win-1251
    # If text has many Р/С chars, it's likely double-encoded
    count_rs = sum(1 for ch in text if ch in ('Р', 'С'))
    if count_rs < 4 or count_rs / max(len(text), 1) < 0.15:
        return text
    try:
        raw = text.encode('cp1251')
        recovered = raw.decode('utf-8', errors='strict')
        # Compare by text_score (quality) and Cyrillic ratio, not raw count
        # (corrupted text has more chars total, so raw count comparison fails)
        new_score = _text_score(recovered)
        old_score = _text_score(text)
        if new_score > old_score:
            return recovered
    except UnicodeEncodeError:
        # Some chars not in cp1251 — try with errors='replace' to encode what we can
        try:
            raw = text.encode('cp1251', errors='replace')
            recovered = raw.decode('utf-8', errors='replace')
            new_score = _text_score(recovered)
            old_score = _text_score(text)
            if new_score > old_score + 0.3:
                return recovered
        except Exception:
            pass
    except UnicodeDecodeError:
        pass
    return text


def _bytes_look_text(payload: bytes) -> bool:
    if not payload:
        return False
    if b"\x00" in payload:
        return False
    sample = payload[:4096]
    printable = 0
    for b in sample:
        if b in (9, 10, 13) or 32 <= b <= 126 or b >= 0x80:
            printable += 1
    return printable / max(len(sample), 1) > 0.72


def _decode_bytes(payload: bytes, charset: str) -> str:
    encodings = []
    if charset:
        encodings.append(charset)
    encodings += ["utf-8", "cp1251", "koi8-r", "iso-8859-5", "windows-1251", "latin1"]
    best_text = ""
    best_score = -1.0
    seen = set()
    for enc in encodings:
        # Normalize encoding name to avoid duplicates
        try:
            norm_enc = codecs.lookup(enc).name
        except (LookupError, Exception):
            norm_enc = enc.lower()
        if norm_enc in seen:
            continue
        seen.add(norm_enc)
        try:
            # First try strict decode — if it works cleanly, give a bonus
            try:
                decoded = payload.decode(enc, errors="strict")
                score = _text_score(decoded) + 0.5  # bonus for clean decode
            except (UnicodeDecodeError, Exception):
                # Fallback to replace so we can see how many errors occurred
                decoded = payload.decode(enc, errors="replace")
                replacement_count = decoded.count("\ufffd")
                score = _text_score(decoded)
                # Penalize for replacement characters (encoding errors)
                if replacement_count > 0:
                    penalty = replacement_count / max(len(decoded), 1)
                    score -= penalty * 4.0
        except Exception:
            continue
        if score > best_score:
            best_score = score
            best_text = decoded
        fixed = _fix_7bit_stripped_cp1251(decoded)
        if fixed != decoded:
            fixed_score = _text_score(fixed)
            if fixed_score > best_score + 0.1:
                best_score = fixed_score
                best_text = fixed
        fixed_mask = _fix_7bit_stripped_cp1251_mask(decoded)
        if fixed_mask != decoded:
            fixed_mask_score = _text_score(fixed_mask)
            if fixed_mask_score > best_score + 0.1:
                best_score = fixed_mask_score
                best_text = fixed_mask
        # Try fixing UTF-8 double-encoded via win-1251
        fixed2 = _fix_utf8_double_encoded_win1251(decoded)
        if fixed2 != decoded:
            fixed2_score = _text_score(fixed2)
            if fixed2_score > best_score + 0.1:
                best_score = fixed2_score
                best_text = fixed2
    # Strip replacement characters from final result
    if best_text:
        best_text = best_text.replace("\ufffd", "")
    # Final pass: try UTF-8 double-encoding fix on the best result
    final_fixed = _fix_utf8_double_encoded_win1251(best_text)
    if final_fixed != best_text:
        if _text_score(final_fixed) > _text_score(best_text):
            best_text = final_fixed
    return best_text


def _is_base64ish(text: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 120:
        return False
    if re.fullmatch(r"[A-Za-z0-9+/=]+", compact or ""):
        return True
    if re.findall(r"[A-Za-z0-9+/=]{80,}", compact):
        return True
    return False


def _decode_base64_payload(text: str, charset: str = "utf-8") -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9+/=]", "", text)
    if len(cleaned) < 40:
        return None
    pad = (-len(cleaned)) % 4
    if pad:
        cleaned += "=" * pad
    try:
        decoded = base64.b64decode(cleaned, validate=False)
        decoded_text = _decode_bytes(decoded, charset)
        if not decoded_text:
            return None
        printable = sum(1 for ch in decoded_text if ch.isprintable() or ch in "\r\n\t")
        if decoded_text and printable / max(len(decoded_text), 1) > 0.65:
            return decoded_text
    except Exception:
        return None
    return None


def _maybe_base64_decode_text(text: str, charset: str = "utf-8") -> str:
    if not text:
        return text
    lower = text.lower()
    marker = "content-transfer-encoding: base64"
    if marker in lower:
        tail = text[lower.find(marker) + len(marker):]
        tail = re.sub(r"^[\s:;]+", "", tail)
        parts = re.split(r"\r?\n\r?\n", tail, maxsplit=1)
        if len(parts) == 2:
            candidate = "".join(re.findall(r"[A-Za-z0-9+/=]{20,}", parts[1]))
            decoded_text = _decode_base64_payload(candidate, charset)
            if decoded_text:
                return decoded_text
        tokens = re.findall(r"[A-Za-z0-9+/=]{20,}", tail)
        if tokens:
            decoded_text = _decode_base64_payload("".join(tokens), charset)
            if decoded_text:
                return decoded_text

    compact = re.sub(r"\s+", "", text)
    if len(compact) > 120:
        decoded_text = _decode_base64_payload(compact, charset)
        if decoded_text:
            return decoded_text
    tokens = re.findall(r"[A-Za-z0-9+/=]{40,}", text)
    if tokens:
        decoded_text = _decode_base64_payload("".join(tokens), charset)
        if decoded_text:
            return decoded_text
    return text


def _maybe_quoted_printable_decode_text(text: str, charset: str = "utf-8") -> str:
    if not text:
        return text
    if not re.search(r"=[0-9A-Fa-f]{2}|=\r?\n", text):
        return text
    try:
        decoded = quopri.decodestring(text.encode("latin1", errors="ignore"))
        decoded_text = _decode_bytes(decoded, charset)
        if decoded_text and _text_score(decoded_text) > _text_score(text):
            return decoded_text
    except Exception:
        return text
    return text


def _cleanup_body_text(text: str, charset: str = "utf-8") -> str:
    if not text:
        return ""
    cleaned = text.replace("\x00", "")
    # Strip common MIME header noise that leaks into body
    cleaned = re.sub(r"(?im)^content-.*$", "", cleaned)
    cleaned = re.sub(r"(?im)^mime-version:.*$", "", cleaned)
    cleaned = re.sub(r"(?im)^boundary=.*$", "", cleaned)
    # Remove long base64 blocks that sometimes leak into body
    cleaned = re.sub(r"[A-Za-z0-9+/=]{200,}", "", cleaned)
    cleaned = cleaned.strip()

    if not cleaned:
        return ""

    # Drop obvious binary/attachment garbage
    if cleaned.lstrip().startswith("%PDF-"):
        return ""
    printable = sum(1 for ch in cleaned if ch.isprintable() or ch in "\r\n\t")
    if printable / max(len(cleaned), 1) < 0.25:
        return ""
    if len(cleaned) > 80:
        letters = sum(1 for ch in cleaned if ch.isalpha())
        spaces = sum(1 for ch in cleaned if ch.isspace())
        if spaces / len(cleaned) < 0.02 and letters / len(cleaned) < 0.2:
            return ""
    if len(cleaned) <= 200:
        letters = sum(1 for ch in cleaned if ch.isalpha())
        digits = sum(1 for ch in cleaned if ch.isdigit())
        spaces = sum(1 for ch in cleaned if ch.isspace())
        if spaces < 2 and (letters + digits) / max(len(cleaned), 1) < 0.2:
            return ""
    # If it still looks like raw base64, drop it.
    if re.fullmatch(r"[A-Za-z0-9+/=\r\n]+", cleaned) and len(cleaned) > 120:
        return ""
    # Try to fix 7-bit stripped CP1251 before gibberish check
    cleaned = _fix_7bit_stripped_cp1251(cleaned)
    cleaned = _fix_7bit_stripped_cp1251_mask(cleaned)
    # Try to fix UTF-8 double-encoded via win-1251
    cleaned = _fix_utf8_double_encoded_win1251(cleaned)
    # Check plain-text representation even when HTML tags exist.
    plain = re.sub(r"<[^>]+>", " ", cleaned)
    if _looks_gibberish(plain):
        return ""
    return cleaned


def _html_visible_text(text: str) -> str:
    if not text:
        return ""
    without_noise = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", text)
    visible = re.sub(r"(?is)<[^>]+>", " ", without_noise)
    visible = html.unescape(visible)
    visible = re.sub(r"\s+", " ", visible).strip()
    return visible


def _cleanup_html_body(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\x00", "").strip()
    if not cleaned:
        return ""
    if cleaned.lstrip().startswith("%PDF-"):
        return ""
    printable = sum(1 for ch in cleaned if ch.isprintable() or ch in "\r\n\t")
    if printable / max(len(cleaned), 1) < 0.25:
        return ""
    visible = _html_visible_text(cleaned)
    if len(visible) >= 20 and _looks_gibberish(visible):
        fixed = _fix_7bit_stripped_cp1251(visible)
        fixed = _fix_7bit_stripped_cp1251_mask(fixed)
        fixed = _fix_utf8_double_encoded_win1251(fixed)
        if fixed and fixed != visible and not _looks_gibberish(fixed):
            return fixed
        return ""
    return cleaned


def _tokenize_bodystructure(src: str) -> List[str]:
    tokens = []
    i = 0
    length = len(src)
    while i < length:
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        if ch in ("(", ")"):
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            buf = []
            while i < length:
                ch = src[i]
                if ch == '"':
                    i += 1
                    break
                if ch == "\\" and i + 1 < length:
                    buf.append(src[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
            tokens.append("".join(buf))
            continue
        # atom
        j = i
        while j < length and not src[j].isspace() and src[j] not in ("(", ")"):
            j += 1
        atom = src[i:j]
        tokens.append(atom)
        i = j
    return tokens


def _parse_bodystructure_tokens(tokens: List[str]):
    idx = 0

    def parse():
        nonlocal idx
        if idx >= len(tokens):
            return None
        tok = tokens[idx]
        if tok == "(":
            idx += 1
            items = []
            while idx < len(tokens) and tokens[idx] != ")":
                items.append(parse())
            if idx < len(tokens) and tokens[idx] == ")":
                idx += 1
            return items
        if tok == "NIL":
            idx += 1
            return None
        idx += 1
        return tok

    return parse()


def _extract_bodystructure(payload: bytes) -> Optional[str]:
    if not payload:
        return None
    try:
        text = payload.decode("utf-8", errors="ignore")
    except Exception:
        return None
    # BODYSTRUCTURE is inside the fetch response, extract after keyword
    match = re.search(r"BODYSTRUCTURE\s+(\(.*\))", text, re.S)
    if match:
        return match.group(1)
    return None


def _is_multipart_node(node) -> bool:
    return isinstance(node, list) and node and isinstance(node[0], list)


def _walk_bodystructure(node, prefix: str = ""):
    if _is_multipart_node(node):
        part_index = 1
        for child in node:
            if not isinstance(child, list):
                break
            part_num = f"{prefix}.{part_index}" if prefix else str(part_index)
            yield from _walk_bodystructure(child, part_num)
            part_index += 1
    else:
        if isinstance(node, list) and len(node) >= 2 and isinstance(node[0], str) and isinstance(node[1], str):
            part_num = prefix or "1"
            yield part_num, node[0].lower(), node[1].lower()


def _fetch_part_text(imap, uid: str, part_no: str) -> Optional[Dict[str, str]]:
    typ, msg_data = imap.uid("fetch", uid, f"(BODY.PEEK[{part_no}.MIME] BODY.PEEK[{part_no}])")
    if not msg_data:
        return None
    header_bytes = b""
    body_bytes = b""
    for part in msg_data:
        if isinstance(part, tuple):
            chunk = part[1] or b""
            if b"Content-Type" in chunk or b"Content-Transfer-Encoding" in chunk:
                header_bytes += chunk
            else:
                body_bytes += chunk
    if not body_bytes:
        return None
    charset = "utf-8"
    content_type = "text/plain"
    cte = ""
    if header_bytes:
        try:
            header_msg = email.message_from_bytes(header_bytes)
            content_type = header_msg.get_content_type() or content_type
            charset = header_msg.get_content_charset() or charset
            cte = (header_msg.get("Content-Transfer-Encoding") or "").lower().strip()
        except Exception:
            pass
    payload = body_bytes
    if cte == "base64":
        try:
            payload = base64.b64decode(body_bytes, validate=False)
        except Exception:
            payload = body_bytes
    elif cte in ("quoted-printable", "quotedprintable", "qp"):
        payload = quopri.decodestring(body_bytes)
    if not _bytes_look_text(payload):
        return None
    decoded = _decode_bytes(payload, charset)
    if _looks_gibberish(decoded):
        decoded = _maybe_base64_decode_text(decoded, charset)
    cleaned = _cleanup_html_body(decoded) if content_type.lower().endswith("html") else _cleanup_body_text(decoded, charset)
    if not cleaned:
        return None
    return {"body": cleaned.strip(), "content_type": content_type}


def normalize_snippet_text(text: str) -> str:
    if not text:
        return ""
    cleaned = _cleanup_body_text(text, "utf-8")
    if not cleaned:
        return ""
    if _looks_gibberish(cleaned):
        return ""
    return cleaned


def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ""
    decoded = []
    for part, enc in decode_header(value):
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            decoded.append(str(part))
    return "".join(decoded).strip()


def _safe_attachment_name(value: Optional[str]) -> str:
    name = _decode_header_value(value or "") or "attachment"
    name = name.replace("\x00", "")
    name = PurePath(name.replace("\\", "/")).name
    name = re.sub(r"[\r\n\t]+", " ", name).strip()
    name = re.sub(r'[<>:"/\\|?*]+', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:180] or "attachment"


def _attachment_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return ("." + filename.rsplit(".", 1)[-1]).lower()


def _is_blocked_attachment(filename: str, content_type: Optional[str]) -> Optional[str]:
    extension = _attachment_extension(filename)
    if extension in BLOCKED_ATTACHMENT_EXTENSIONS:
        return "Тип файла заблокирован политикой безопасности"
    normalized_type = (content_type or "").lower().strip()
    if normalized_type in {"text/html", "image/svg+xml", "application/x-msdownload"}:
        return "MIME-тип заблокирован политикой безопасности"
    return None


def _is_attachment_part(part) -> bool:
    if part.is_multipart():
        return False
    disposition = (part.get("Content-Disposition") or "").lower()
    filename = part.get_filename()
    content_type = (part.get_content_type() or "").lower()
    if "attachment" in disposition:
        return True
    if filename:
        return True
    if "inline" in disposition and filename:
        return True
    if content_type in {"application/pdf", "application/octet-stream"} and filename:
        return True
    return False


def _iter_leaf_parts(message, prefix: str = ""):
    if message.is_multipart():
        payload = message.get_payload() or []
        if not isinstance(payload, list):
            return
        for idx, child in enumerate(payload, start=1):
            part_id = f"{prefix}.{idx}" if prefix else str(idx)
            yield from _iter_leaf_parts(child, part_id)
        return
    yield prefix or "1", message


def _attachment_meta(part_id: str, part, size: Optional[int] = None) -> Dict:
    filename = _safe_attachment_name(part.get_filename())
    content_type = part.get_content_type() or "application/octet-stream"
    blocked_reason = _is_blocked_attachment(filename, content_type)
    if size is None:
        payload = part.get_payload(decode=True) or b""
        size = len(payload)
    if size and size > MAX_ATTACHMENT_BYTES:
        blocked_reason = f"Файл больше лимита {MAX_ATTACHMENT_BYTES // (1024 * 1024)} МБ"
    return {
        "id": str(part_id),
        "name": filename,
        "size": int(size or 0),
        "content_type": content_type,
        "blocked": bool(blocked_reason),
        "blocked_reason": blocked_reason,
        "download_url": f"/api/v1/mail/messages/{{message_id}}/attachments/{part_id}",
    }


def _extract_attachment_metadata(raw_message: bytes, message_id: Optional[str] = None) -> List[Dict]:
    if not raw_message:
        return []
    msg = email.message_from_bytes(raw_message)
    attachments: List[Dict] = []
    for part_id, part in _iter_leaf_parts(msg):
        if not _is_attachment_part(part):
            continue
        meta = _attachment_meta(part_id, part)
        if message_id:
            meta["download_url"] = f"/api/v1/mail/messages/{message_id}/attachments/{part_id}"
        attachments.append(meta)

        filename = (meta.get("name") or "").lower()
        content_type = (meta.get("content_type") or "").lower()
        if content_type == "text/html" or filename.endswith((".html", ".htm")):
            payload = part.get_payload(decode=True) or b""
            if payload and len(payload) <= 1024 * 1024:
                charset = part.get_content_charset() or "utf-8"
                decoded = _decode_bytes(payload, charset)
                for link in _extract_external_attachment_links(decoded, "", require_hint=False):
                    link["id"] = f"{part_id}-{link['id']}"
                    attachments.append(link)
    return attachments


def _strip_tags(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return html.unescape(" ".join(value.split())).strip()


def _safe_external_attachment_url(url: str) -> Optional[str]:
    url = html.unescape(str(url or "")).strip()
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    if parsed.scheme.lower() != "https":
        return None
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        return None
    if not any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_EXTERNAL_ATTACHMENT_HOST_SUFFIXES):
        return None
    return url


def _external_attachment_name(url: str, label: str = "") -> str:
    label = _strip_tags(label)
    if label and not re.fullmatch(r"https?://\S+", label, re.I):
        return label[:180]
    try:
        parsed = urlparse(url)
        path_name = unquote(PurePath(parsed.path or "").name or "")
    except Exception:
        path_name = ""
    return (path_name or "Файл по ссылке")[:180]


def _external_attachment_meta(url: str, label: str = "", index: int = 0) -> Dict:
    name = _external_attachment_name(url, label)
    return {
        "id": f"link-{index}",
        "name": name,
        "size": None,
        "content_type": "external/link",
        "blocked": False,
        "blocked_reason": None,
        "download_url": None,
        "external_url": url,
        "external": True,
    }


def _extract_external_attachment_links(html_body: str = "", text_body: str = "", require_hint: bool = True) -> List[Dict]:
    found: List[Dict] = []
    seen = set()

    def add(url: str, label: str = ""):
        safe = _safe_external_attachment_url(url)
        if not safe or safe in seen:
            return
        hint_source = f"{label} {safe}"
        if require_hint and not FILE_LINK_HINT_RE.search(hint_source):
            return
        seen.add(safe)
        found.append(_external_attachment_meta(safe, label, len(found) + 1))

    for match in re.finditer(r"""<a\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>""", html_body or "", re.I | re.S):
        add(match.group(1), match.group(2))

    for match in re.finditer(r"https://[^\s<>'\")]+", f"{html_body or ''}\n{text_body or ''}"):
        add(match.group(0), "")

    return found


def _bodystructure_attachment_count(value: Optional[str]) -> int:
    if not value:
        return 0
    text = value.upper()
    count = len(re.findall(r'"ATTACHMENT"', text))
    if count:
        return count
    return len(re.findall(r'"FILENAME"\s+"[^"]+"', text))


def _header_suggests_attachment(msg) -> bool:
    content_type = (msg.get("Content-Type") or "").lower()
    disposition = (msg.get("Content-Disposition") or "").lower()
    return (
        "multipart/mixed" in content_type
        or "multipart/related" in content_type
        or "name=" in content_type
        or "attachment" in disposition
        or "filename=" in disposition
    )


def _format_addresses(value: Optional[str]) -> str:
    if not value:
        return ""
    items = []
    for name, addr in getaddresses([value]):
        name = _decode_header_value(name)
        if name:
            items.append(f"{name} <{addr}>")
        else:
            items.append(addr)
    return ", ".join([i for i in items if i])


def _auth_string(email_addr: str, access_token: str) -> bytes:
    email_addr = email_addr.strip().lower()
    raw = f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(raw.encode("utf-8"))


def _decode_snippet(snippet_bytes: bytes, header_bytes: bytes) -> str:
    if not snippet_bytes:
        return ""
    try:
        header_msg = email.message_from_bytes(header_bytes)
    except Exception:
        header_msg = None

    charset = "utf-8"
    cte = ""
    if header_msg:
        charset = header_msg.get_content_charset() or "utf-8"
        cte = (header_msg.get("Content-Transfer-Encoding") or "").lower().strip()

    raw_bytes = snippet_bytes
    if cte == "base64":
        try:
            raw_bytes = base64.b64decode(snippet_bytes, validate=False)
        except Exception:
            raw_bytes = snippet_bytes
    elif cte in ("quoted-printable", "quotedprintable", "qp"):
        raw_bytes = quopri.decodestring(snippet_bytes)

    # If body chunk contains its own MIME headers, parse as a message part.
    if b"Content-Transfer-Encoding" in snippet_bytes or b"Content-Type" in snippet_bytes:
        try:
            part = email.message_from_bytes(snippet_bytes)
            if part.is_multipart():
                payload = None
                for sub in part.walk():
                    if sub.get_content_maintype() == "text":
                        payload = sub.get_payload(decode=True)
                        charset = sub.get_content_charset() or charset
                        if payload:
                            break
            else:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or charset
            if payload:
                snippet = _decode_bytes(payload, charset)
            else:
                snippet = _decode_bytes(raw_bytes, charset)
        except Exception:
            snippet = _decode_bytes(raw_bytes, charset)
    else:
        snippet = _decode_bytes(raw_bytes, charset)

    def _decode_base64_payload_inner(text: str) -> Optional[str]:
        if not text:
            return None
        cleaned = re.sub(r"[^A-Za-z0-9+/=]", "", text)
        if len(cleaned) < 40:
            return None
        pad = (-len(cleaned)) % 4
        if pad:
            cleaned += "=" * pad
        try:
            decoded = base64.b64decode(cleaned, validate=False)
            decoded_text = _decode_bytes(decoded, charset)
            if not decoded_text:
                return None
            printable = sum(1 for ch in decoded_text if ch.isprintable())
            if decoded_text and printable / max(len(decoded_text), 1) > 0.65:
                return decoded_text
        except Exception:
            return None
        return None

    def _maybe_base64_decode(text: str) -> str:
        if not text:
            return text
        lower = text.lower()
        marker = "content-transfer-encoding: base64"
        if marker in lower:
            tail = text[lower.find(marker) + len(marker):]
            tail = re.sub(r"^[\\s:;]+", "", tail)
            # If the body includes a blank line, decode everything after it.
            parts = re.split(r"\r?\n\r?\n", tail, maxsplit=1)
            if len(parts) == 2:
                candidate = "".join(re.findall(r"[A-Za-z0-9+/=]{20,}", parts[1]))
                decoded_text = _decode_base64_payload_inner(candidate)
                if decoded_text:
                    return decoded_text
            # Decode concatenated base64 tokens that follow the marker.
            tokens = re.findall(r"[A-Za-z0-9+/=]{20,}", tail)
            if tokens:
                decoded_text = _decode_base64_payload_inner("".join(tokens))
                if decoded_text:
                    return decoded_text

        # Heuristic: raw base64 without spaces
        compact = re.sub(r"\s+", "", text)
        if len(compact) > 120:
            decoded_text = _decode_base64_payload_inner(compact)
            if decoded_text:
                return decoded_text
        # Heuristic: decode any long base64 token chunks
        tokens = re.findall(r"[A-Za-z0-9+/=]{40,}", text)
        if tokens:
            decoded_text = _decode_base64_payload_inner("".join(tokens))
            if decoded_text:
                return decoded_text
        return text

    # Remove MIME technical headers if they leaked into snippet
    snippet = _maybe_base64_decode(snippet)
    snippet = re.sub(r"(?im)^content-.*$", "", snippet)
    snippet = re.sub(r"(?im)^mime-version:.*$", "", snippet)
    snippet = re.sub(r"(?im)^boundary=.*$", "", snippet)
    snippet = re.sub(r"(?im)^--[-_A-Za-z0-9]+.*$", "", snippet)
    snippet = " ".join(snippet.strip().split())
    return normalize_snippet_text(snippet)


FOLDER_DEFINITIONS = {
    "inbox": {"label": "Входящие", "candidates": ["INBOX"]},
    "sent": {
        "label": "Отправленные",
        "candidates": ["&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-", "Sent", "Sent Messages"],
    },
    "archive": {
        "label": "Архив",
        "candidates": ["&BBAEQARFBDgEMg-", "Archive"],
    },
    "spam": {
        "label": "Спам",
        "candidates": ["&BCEEPwQwBDw-", "Spam", "Junk", "Junk E-mail"],
    },
    "trash": {
        "label": "Корзина",
        "candidates": ["&BCMENAQwBDsENQQ9BD0ESwQ1-", "Trash", "Deleted", "Deleted Messages"],
    },
    "drafts": {
        "label": "Черновики",
        "candidates": ["&BCcENQRABD0EPgQyBDgEOgQ4-", "Drafts"],
    },
}


def _imap_connect(email_addr: str, access_token: str, auth_mode: str = "oauth", password: Optional[str] = None):
    host = IMAP_HOST
    try:
        info = socket.getaddrinfo(IMAP_HOST, IMAP_PORT, socket.AF_INET, socket.SOCK_STREAM)
        if info:
            host = info[0][4][0]
    except Exception:
        host = IMAP_HOST

    imap = imaplib.IMAP4_SSL(host, IMAP_PORT, timeout=20)
    if auth_mode == "password":
        imap.login(email_addr, password or "")
    else:
        imap.authenticate("XOAUTH2", lambda _: _auth_string(email_addr, access_token))
    return imap


def _folder_candidates(folder: str) -> List[str]:
    folder = (folder or "inbox").strip().lower()
    if folder in FOLDER_DEFINITIONS:
        return list(FOLDER_DEFINITIONS[folder]["candidates"])
    return [folder]


def _select_folder(imap, folder: str, readonly: bool = True) -> str:
    last_error = None
    for candidate in _folder_candidates(folder):
        try:
            typ, _ = imap.select(candidate, readonly=readonly)
            if typ == "OK":
                return candidate
            last_error = typ
        except Exception as exc:
            last_error = exc
    raise ValueError(f"mail_folder_not_found:{folder}:{last_error}")


def _parse_copyuid(data) -> Optional[str]:
    text_parts = []
    for item in data or []:
        if isinstance(item, bytes):
            text_parts.append(item.decode("utf-8", errors="ignore"))
        else:
            text_parts.append(str(item))
    text = " ".join(text_parts)
    match = re.search(r"COPYUID\s+\d+\s+\d+\s+(\d+)", text)
    return match.group(1) if match else None


def move_message_to_folder(
    email_addr: str,
    access_token: str,
    uid: str,
    source_folder: str,
    target_folder: str,
    auth_mode: str = "oauth",
    password: Optional[str] = None,
) -> Optional[str]:
    imap = _imap_connect(email_addr, access_token, auth_mode, password)
    try:
        _select_folder(imap, source_folder, readonly=False)
        target_name = None
        last_error = None
        for candidate in _folder_candidates(target_folder):
            try:
                typ, _ = imap.select(candidate, readonly=True)
                if typ == "OK":
                    target_name = candidate
                    break
                last_error = typ
            except Exception as exc:
                last_error = exc
        if not target_name:
            if target_folder == "archive":
                target_name = _folder_candidates(target_folder)[0]
                typ, data = imap.create(target_name)
                if typ != "OK":
                    raise ValueError(f"mail_folder_not_found:{target_folder}:{last_error}:{data}")
            else:
                raise ValueError(f"mail_folder_not_found:{target_folder}:{last_error}")

        _select_folder(imap, source_folder, readonly=False)
        typ, data = imap.uid("MOVE", uid, target_name)
        if typ == "OK":
            return _parse_copyuid(data)

        typ, data = imap.uid("COPY", uid, target_name)
        if typ != "OK":
            raise ValueError(f"mail_move_failed:{typ}:{data}")
        copied_uid = _parse_copyuid(data)
        typ, data = imap.uid("STORE", uid, "+FLAGS", r"(\Deleted)")
        if typ != "OK":
            raise ValueError(f"mail_delete_flag_failed:{typ}:{data}")
        imap.expunge()
        return copied_uid
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def fetch_recent_messages(
    email_addr: str,
    access_token: str,
    last_uid: Optional[str] = None,
    limit: int = 50,
    since_dt: Optional[datetime] = None,
    mailbox: str = "INBOX",
    auth_mode: str = "oauth",
    password: Optional[str] = None,
) -> List[Dict]:
    imap = _imap_connect(email_addr, access_token, auth_mode, password)
    try:
        _select_folder(imap, mailbox, readonly=True)
    except ValueError:
        if (mailbox or "").strip().lower() in FOLDER_DEFINITIONS and (mailbox or "").strip().lower() != "inbox":
            try:
                imap.logout()
            except Exception:
                pass
            return []
        raise

    search_criteria = "ALL"
    if last_uid:
        try:
            last_val = int(last_uid)
            search_criteria = f"UID {last_val + 1}:*"
        except ValueError:
            search_criteria = "ALL"
    elif since_dt:
        search_criteria = f"SINCE {since_dt.strftime('%d-%b-%Y')}"

    typ, data = imap.uid("search", None, search_criteria)
    uids = []
    if data and data[0]:
        uids = data[0].split()

    if limit and len(uids) > limit:
        uids = uids[-limit:]

    items = []
    for uid in uids:
        uid_str = uid.decode("utf-8") if isinstance(uid, bytes) else str(uid)
        typ, msg_data = imap.uid(
            "fetch",
            uid,
            "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO CC DATE MESSAGE-ID CONTENT-TYPE CONTENT-TRANSFER-ENCODING)] BODY.PEEK[TEXT]<0.4096> BODYSTRUCTURE FLAGS)",
        )
        if not msg_data:
            continue
        header_bytes = b""
        snippet_bytes = b""
        flags = ""
        bodystructure_src = ""
        for part in msg_data:
            if isinstance(part, tuple):
                content = part[1] or b""
                if b"Subject:" in content or b"From:" in content:
                    header_bytes += content
                elif b"BODYSTRUCTURE" in content:
                    bodystructure_src += content.decode("utf-8", errors="ignore")
                else:
                    snippet_bytes += content
            elif isinstance(part, bytes):
                text = part.decode("utf-8", errors="ignore")
                if "FLAGS" in text:
                    flags = text
                if "BODYSTRUCTURE" in text:
                    bodystructure_src += text
        msg = email.message_from_bytes(header_bytes)
        subject = _decode_header_value(msg.get("Subject"))
        from_addr = _format_addresses(msg.get("From"))
        to_addr = _format_addresses(msg.get("To"))
        cc_addr = _format_addresses(msg.get("Cc"))
        message_id = msg.get("Message-ID")
        date = None
        try:
            date = parsedate_to_datetime(msg.get("Date"))
        except Exception:
            date = None
        snippet = _decode_snippet(snippet_bytes, header_bytes)
        attachments_count = _bodystructure_attachment_count(bodystructure_src)
        has_attachments = attachments_count > 0 or _header_suggests_attachment(msg)

        items.append({
            "uid": uid_str,
            "subject": subject,
            "from_addr": from_addr,
            "to_addr": to_addr,
            "cc_addr": cc_addr,
            "date": date,
            "message_id": message_id,
            "snippet": snippet[:500] if snippet else "",
            "flags": flags,
            "has_attachments": bool(has_attachments),
            "attachments_count": attachments_count,
        })

    try:
        imap.close()
    except Exception:
        pass
    imap.logout()
    return items


def fetch_message_body(
    email_addr: str,
    access_token: str,
    uid: str,
    mailbox: str = "INBOX",
    auth_mode: str = "oauth",
    password: Optional[str] = None,
    message_id: Optional[str] = None,
) -> Dict:
    imap = _imap_connect(email_addr, access_token, auth_mode, password)
    _select_folder(imap, mailbox, readonly=True)

    typ, msg_data = imap.uid("fetch", uid, "(BODY.PEEK[])")
    raw_message = b""
    for part in msg_data or []:
        if isinstance(part, tuple):
            raw_message += part[1] or b""

    text_body = None
    html_body = None
    cc_addr = ""
    attachments = _extract_attachment_metadata(raw_message, message_id)

    def _decode_part(part, is_html: bool = False) -> str:
        payload = part.get_payload(decode=True) or b""
        if not _bytes_look_text(payload):
            return ""
        charset = part.get_content_charset() or "utf-8"
        decoded = _decode_bytes(payload, charset)
        if _is_base64ish(decoded):
            decoded = _maybe_base64_decode_text(decoded, charset)
        if re.search(r"=[0-9A-Fa-f]{2}|=\r?\n", decoded or ""):
            decoded = _maybe_quoted_printable_decode_text(decoded, charset)
        if _looks_gibberish(decoded):
            decoded = _maybe_base64_decode_text(decoded, charset)
        if _looks_gibberish(decoded):
            decoded = _maybe_quoted_printable_decode_text(decoded, charset)
        return _cleanup_html_body(decoded) if is_html else _cleanup_body_text(decoded, charset)

    if raw_message:
        msg = email.message_from_bytes(raw_message)
        cc_addr = _format_addresses(msg.get("Cc"))
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type.startswith("multipart/"):
                    continue
                disposition = (part.get("Content-Disposition") or "").lower()
                if "attachment" in disposition:
                    continue
                if content_type == "text/plain" and text_body is None:
                    candidate = _decode_part(part)
                    if candidate and _text_score(candidate) > _text_score(text_body or ""):
                        text_body = candidate
                elif content_type == "text/html" and html_body is None:
                    candidate = _decode_part(part, is_html=True)
                    candidate_score = _text_score(_html_visible_text(candidate) or candidate)
                    current_score = _text_score(_html_visible_text(html_body or "") or (html_body or ""))
                    if candidate and candidate_score >= current_score:
                        html_body = candidate
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                text_body = _decode_part(msg)
            elif content_type == "text/html":
                html_body = _decode_part(msg, is_html=True)

    # Fallback: use BODYSTRUCTURE to fetch text parts directly (some messages return empty BODY[]).
    if not text_body and not html_body:
        typ, bs_data = imap.uid("fetch", uid, "(BODYSTRUCTURE)")
        bs_src = _extract_bodystructure(bs_data[0] if bs_data else b"")
        if bs_src:
            tokens = _tokenize_bodystructure(bs_src)
            parsed = _parse_bodystructure_tokens(tokens)
            parts = list(_walk_bodystructure(parsed))
            html_parts = [p for p in parts if p[1] == "text" and p[2] == "html"]
            text_parts = [p for p in parts if p[1] == "text" and p[2] == "plain"]
            for part_no, _, _ in html_parts + text_parts:
                fetched = _fetch_part_text(imap, uid, part_no)
                if not fetched:
                    continue
                if fetched["content_type"].lower().endswith("html") and not html_body:
                    html_body = fetched["body"]
                elif not text_body:
                    text_body = fetched["body"]
                if html_body or text_body:
                    break

    try:
        imap.close()
    except Exception:
        pass
    imap.logout()

    attachments.extend(_extract_external_attachment_links(html_body or "", text_body or ""))

    if html_body:
        body = html_body.strip()
        return {"body": body, "body_html": body, "content_type": "text/html", "attachments": attachments, "cc_addr": cc_addr}
    if text_body:
        if re.search(r"</?(html|body|head|div|p|table|br|span)\b", text_body, re.I) or re.search(r"<!doctype", text_body, re.I):
            body = text_body.strip()
            return {"body": body, "body_html": body, "content_type": "text/html", "attachments": attachments, "cc_addr": cc_addr}
        body = text_body.strip()
        return {"body": body, "body_text": body, "content_type": "text/plain", "attachments": attachments, "cc_addr": cc_addr}
    if html_body:
        body = html_body.strip()
        return {"body": body, "body_html": body, "content_type": "text/html", "attachments": attachments, "cc_addr": cc_addr}

    return {"body": "", "body_text": "", "content_type": "text/plain", "attachments": attachments, "cc_addr": cc_addr}


def fetch_message_attachment(
    email_addr: str,
    access_token: str,
    uid: str,
    attachment_id: str,
    mailbox: str = "INBOX",
    auth_mode: str = "oauth",
    password: Optional[str] = None,
) -> Dict:
    if not re.fullmatch(r"\d+(?:\.\d+)*", str(attachment_id or "")):
        raise ValueError("invalid_attachment_id")

    imap = _imap_connect(email_addr, access_token, auth_mode, password)
    try:
        _select_folder(imap, mailbox, readonly=True)

        typ, msg_data = imap.uid(
            "fetch",
            uid,
            f"(BODY.PEEK[{attachment_id}.MIME] BODY.PEEK[{attachment_id}])",
        )
        if typ != "OK" or not msg_data:
            raise ValueError("attachment_not_found")

        header_bytes = b""
        body_bytes = b""
        for part in msg_data:
            if not isinstance(part, tuple):
                continue
            chunk = part[1] or b""
            if b"Content-Type" in chunk or b"Content-Disposition" in chunk or b"Content-Transfer-Encoding" in chunk:
                header_bytes += chunk
            else:
                body_bytes += chunk

        if not header_bytes or not body_bytes:
            raise ValueError("attachment_not_found")

        header_msg = email.message_from_bytes(header_bytes)
        if not _is_attachment_part(header_msg):
            raise ValueError("attachment_not_found")

        filename = _safe_attachment_name(header_msg.get_filename())
        content_type = header_msg.get_content_type() or "application/octet-stream"
        blocked_reason = _is_blocked_attachment(filename, content_type)
        if blocked_reason:
            raise PermissionError(blocked_reason)

        cte = (header_msg.get("Content-Transfer-Encoding") or "").lower().strip()
        payload = body_bytes
        if cte == "base64":
            payload = base64.b64decode(body_bytes, validate=False)
        elif cte in ("quoted-printable", "quotedprintable", "qp"):
            payload = quopri.decodestring(body_bytes)

        if len(payload) > MAX_ATTACHMENT_BYTES:
            raise ValueError("attachment_too_large")

        return {
            "filename": filename,
            "content_type": content_type,
            "content": payload,
        }
    finally:
        try:
            imap.close()
        except Exception:
            pass
        imap.logout()
