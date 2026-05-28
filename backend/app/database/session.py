"""
Database session configuration
"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, StaticPool

from app.core.config import settings

db_url = settings.SQLALCHEMY_DATABASE_URI
is_sqlite = db_url.startswith("sqlite://")
is_memory_sqlite = is_sqlite and (":memory:" in db_url or db_url.endswith("sqlite://"))

async_db_url = db_url
engine_kwargs = {"echo": False}
connect_args = {}

if is_sqlite:
    async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    connect_args = {"check_same_thread": False}
    if is_memory_sqlite:
        # In-memory SQLite MUST share one connection or the schema vanishes.
        engine_kwargs["poolclass"] = StaticPool
    else:
        # File-backed SQLite: a real pool gives concurrent requests their
        # own aiosqlite connection (each runs its own thread). Combined
        # with WAL + busy_timeout below this removes the single-connection
        # serialization and the "SQL statements in progress" 500s.
        # (Async SQLite defaults to NullPool, which rejects pool sizing —
        # so the queue pool class must be set explicitly.)
        engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
        engine_kwargs["pool_size"] = settings.SQLITE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.SQLITE_MAX_OVERFLOW
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 1800
else:
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

engine_kwargs["connect_args"] = connect_args

engine = create_async_engine(async_db_url, **engine_kwargs)

if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _apply_sqlite_pragmas(dbapi_connection, _connection_record):
        """Per-connection SQLite tuning. WAL = readers don't block on a
        writer; busy_timeout = writers wait-and-retry instead of an
        instant 'database is locked'; synchronous=NORMAL is safe under
        WAL and much faster; foreign_keys keeps integrity on."""
        cur = dbapi_connection.cursor()
        try:
            if not is_memory_sqlite:
                cur.execute("PRAGMA journal_mode=WAL")
            cur.execute(f"PRAGMA busy_timeout={int(settings.SQLITE_BUSY_TIMEOUT_MS)}")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA foreign_keys=ON")
        finally:
            cur.close()

# Create async session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for migrations (Alembic)
from sqlalchemy import create_engine
engine_sync_kwargs = {}
if is_sqlite:
    engine_sync_kwargs["connect_args"] = {"check_same_thread": False}
engine_sync = create_engine(db_url, **engine_sync_kwargs)

# Dependency for FastAPI
async def get_db():
    """Dependency for getting async database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
