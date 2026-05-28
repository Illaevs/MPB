"""
Application configuration settings
"""
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings

_CONFIG_BASE_DIR = Path(__file__).resolve().parents[3]
_CONFIG_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    APP_VARIANT: str = "default"
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # default 1 hour
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES: int = 20
    TWO_FACTOR_ISSUER: str = "Nexustech"
    REQUIRE_TWO_FACTOR: bool = True
    ACCESS_COOKIE_NAME: str = "crm_access_token"
    REFRESH_COOKIE_NAME: str = "crm_refresh_token"
    CSRF_COOKIE_NAME: str = "crm_csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    AUTH_COOKIE_SECURE: bool = True
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_COOKIE_DOMAIN: Optional[str] = None
    ACCESS_COOKIE_PATH: str = "/api"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth/refresh"
    CSRF_COOKIE_PATH: str = "/"
    SECURITY_CSP: str = (
        "default-src 'self'; "
        "img-src 'self' data: blob: https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "script-src 'self'; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https: ws: wss:; "
        "media-src 'self' data: blob: https:; "
        "worker-src 'self' blob:; "
        "manifest-src 'self'; "
        "frame-src 'self' blob: data:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'"
    )

    # Database
    _BASE_DIR = _CONFIG_BASE_DIR
    _DEFAULT_DB_PATH = _BASE_DIR / "crm.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{_DEFAULT_DB_PATH.as_posix()}"  # SQLite for development
    # For PostgreSQL production: "postgresql://user:password@localhost/crm"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Vue dev server
        "http://localhost:3001",
        "http://localhost:8080",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "https://for-apps.ru",
        "https://www.for-apps.ru",
    ]
    CSRF_EXEMPT_PATHS: List[str] = [
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/verify-2fa",
        # Event-bus test-sink — synthetic webhook-receiver, без сессии и CSRF.
        "/api/v1/event-bus/_test/webhook-sink",
    ]

    # Project settings
    PROJECT_NAME: str = "Construction CRM"
    PROJECT_VERSION: str = "1.0.0"
    PUBLIC_APP_URL: str = "https://for-apps.ru"

    # Yandex OAuth (Mail)
    YANDEX_OAUTH_CLIENT_ID: str = ""
    YANDEX_OAUTH_CLIENT_SECRET: str = ""
    YANDEX_OAUTH_REDIRECT_URI: str = ""
    YANDEX_OAUTH_SCOPES: str = "mail:imap_ro mail:smtp"
    # Legacy env vars kept for compatibility with existing server .env
    YANDEX_TOKEN: str = ""
    YANDEX_ROOT_PATH: str = ""

    # Storage backend (local only)
    STORAGE_BACKEND: str = ""
    # Local storage root (used when STORAGE_BACKEND=local)
    STORAGE_LOCAL_ROOT: str = ""
    STATIC_LOCAL_ROOT: str = ""

    # Dadata integration
    DADATA_TOKEN: str = ""

    # Outgoing registry
    OUTGOING_NUMBER_START: int = 1193
    KP_NUMBER_START: int = 600

    # Upload queue (temporary storage)
    UPLOAD_TMP_DIR: str = ""
    UPLOAD_TMP_MAX_BYTES: int = 256 * 1024 * 1024
    UPLOAD_TMP_TOTAL_MAX_BYTES: int = 5 * 1024 * 1024 * 1024
    UPLOAD_TMP_TTL_HOURS: int = 24

    # Mail sync
    MAIL_POLL_INTERVAL_SECONDS: int = 60
    MAIL_SMTP_HOST: str = "smtp.yandex.ru"
    MAIL_SMTP_SSL_PORT: int = 465
    MAIL_SMTP_TLS_PORT: int = 587
    MAIL_SMTP_TIMEOUT_SECONDS: int = 5
    REDIS_URL: str = ""
    # When True the app refuses to start without a working Redis, so token
    # revocation / logout / rate-limit state is shared and survives restarts
    # and multiple workers. Default False to avoid taking down an existing
    # deployment that has no Redis — but such a deployment MUST run a single
    # worker and treat logout/“revoke sessions” as best-effort (see H4).
    REQUIRE_PERSISTENT_SECURITY_STORE: bool = False
    SECURITY_REDIS_PREFIX: str = "crm"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    TELEGRAM_API_BASE_URL: str = "https://api.telegram.org"
    TELEGRAM_API_TIMEOUT_SECONDS: int = 15
    TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES: int = 30
    TELEGRAM_WEBHOOK_SECRET: str = ""
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "ollama"
    AI_OLLAMA_BASE_URL: str = ""
    AI_MODEL: str = "qwen3:8b"
    AI_TIMEOUT_SECONDS: int = 90
    AI_VERIFY_SSL: bool = True
    API_RATE_LIMIT_READ_REQUESTS: int = 1200
    API_RATE_LIMIT_WRITE_REQUESTS: int = 300
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- SQLite concurrency tuning (ignored on Postgres) ---
    # WAL + busy_timeout let readers run during a write and make writers
    # wait-and-retry instead of erroring; a real connection pool (instead
    # of one shared StaticPool connection) gives true read concurrency.
    SQLITE_BUSY_TIMEOUT_MS: int = 12000
    SQLITE_POOL_SIZE: int = 8
    SQLITE_MAX_OVERFLOW: int = 16
    # Bound concurrent executor file-upload handlers so a burst of
    # simultaneous uploads queues gracefully instead of stampeding
    # SQLite writes. <= 0 disables the limiter.
    UPLOAD_MAX_CONCURRENCY: int = 3
    # Bounded retries for the racy MAX(number)+1 task-number assignment.
    TASK_NUMBER_MAX_RETRIES: int = 8

    # Number of trusted reverse-proxy hops in front of the app (e.g. nginx).
    # The real client IP is taken from X-Forwarded-For as the entry this many
    # hops from the right (the part the trusted proxy itself appended). A
    # client-supplied X-Forwarded-For prefix can no longer spoof the bucket.
    # 0 disables X-Forwarded-For trust entirely (use the raw socket peer).
    TRUSTED_PROXY_HOPS: int = 1

    class Config:
        env_file = (_CONFIG_BACKEND_DIR / ".env", _CONFIG_BASE_DIR / ".env")
        case_sensitive = True
        extra = "ignore"


settings = Settings()

_DEFAULT_SECRET_KEY = "your-secret-key-here-change-in-production"
if settings.SECRET_KEY == _DEFAULT_SECRET_KEY or len(settings.SECRET_KEY) < 64:
    raise RuntimeError(
        "SECRET_KEY должен быть заменен на криптографически стойкий ключ длиной не менее 64 символов."
    )
