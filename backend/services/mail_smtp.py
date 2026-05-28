"""
SMTP helper for Yandex Mail via OAuth2.
"""
import base64
import socket
import smtplib
from email.message import EmailMessage
from typing import List

from app.core.config import settings

SMTP_HOST = settings.MAIL_SMTP_HOST
SMTP_SSL_PORT = settings.MAIL_SMTP_SSL_PORT
SMTP_TLS_PORT = settings.MAIL_SMTP_TLS_PORT
SMTP_TIMEOUT = settings.MAIL_SMTP_TIMEOUT_SECONDS


class MailSendTransportError(RuntimeError):
    """Raised when SMTP transport is unavailable from the server."""


class MailSendAuthenticationError(RuntimeError):
    """Raised when SMTP credentials are rejected."""


def _resolve_ipv4(host: str, port: int) -> str:
    try:
        info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        if info:
            return info[0][4][0]
    except Exception:
        return host
    return host


def _auth_string(email_addr: str, access_token: str) -> str:
    email_addr = email_addr.strip().lower()
    raw = f"user={email_addr}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def _smtp_auth(smtp, email_addr: str, access_token: str, auth_mode: str, password: str):
    try:
        if auth_mode == "password":
            smtp.login(email_addr, password)
        else:
            code, response = smtp.docmd("AUTH", "XOAUTH2 " + _auth_string(email_addr, access_token))
            if code != 235:
                raise smtplib.SMTPAuthenticationError(code, response)
    except smtplib.SMTPAuthenticationError as exc:
        raise MailSendAuthenticationError(str(exc)) from exc


def _describe_error(exc: Exception) -> str:
    message = str(exc).strip()
    if isinstance(exc, socket.timeout) or "timed out" in message.lower():
        return "timeout"
    if isinstance(exc, OSError):
        return f"{exc.__class__.__name__}: {message}"
    return f"{exc.__class__.__name__}: {message}"


def send_message(
    email_addr: str,
    access_token: str,
    to_list: List[str],
    subject: str,
    body: str,
    cc_list: List[str] = None,
    bcc_list: List[str] = None,
    auth_mode: str = "oauth",
    password: str = "",
):
    cc_list = cc_list or []
    bcc_list = bcc_list or []
    msg = EmailMessage()
    msg["From"] = email_addr
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject
    msg.set_content(body)

    all_recipients = list(to_list) + list(cc_list) + list(bcc_list)

    # Try SSL first, then STARTTLS. On some VPS providers outbound SMTP is
    # silently blocked, so keep per-attempt timeout short and preserve context.
    errors = []

    host = _resolve_ipv4(SMTP_HOST, SMTP_SSL_PORT)

    try:
        with smtplib.SMTP_SSL(host, SMTP_SSL_PORT, timeout=SMTP_TIMEOUT) as smtp:
            smtp.ehlo()
            _smtp_auth(smtp, email_addr, access_token, auth_mode, password)
            smtp.send_message(msg, from_addr=email_addr, to_addrs=all_recipients)
            return
    except MailSendAuthenticationError:
        raise
    except Exception as exc:
        errors.append(f"ssl:{SMTP_SSL_PORT} {_describe_error(exc)}")

    # Fallback to STARTTLS on 587
    try:
        tls_host = _resolve_ipv4(SMTP_HOST, SMTP_TLS_PORT)
        with smtplib.SMTP(tls_host, SMTP_TLS_PORT, timeout=SMTP_TIMEOUT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            _smtp_auth(smtp, email_addr, access_token, auth_mode, password)
            smtp.send_message(msg, from_addr=email_addr, to_addrs=all_recipients)
            return
    except MailSendAuthenticationError:
        raise
    except Exception as exc:
        errors.append(f"starttls:{SMTP_TLS_PORT} {_describe_error(exc)}")

    # Last fallback: try hostname directly (in case IP routing differs).
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_TLS_PORT, timeout=SMTP_TIMEOUT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            _smtp_auth(smtp, email_addr, access_token, auth_mode, password)
            smtp.send_message(msg, from_addr=email_addr, to_addrs=all_recipients)
            return
    except MailSendAuthenticationError:
        raise
    except Exception as exc:
        errors.append(f"hostname:{SMTP_TLS_PORT} {_describe_error(exc)}")

    raise MailSendTransportError("; ".join(errors) or "SMTP transport unavailable")
