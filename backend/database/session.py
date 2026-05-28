"""
Database session configuration
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

db_url = settings.SQLALCHEMY_DATABASE_URI
is_sqlite = db_url.startswith("sqlite://")

async_db_url = db_url
engine_kwargs = {"echo": False}
connect_args = {}

if is_sqlite:
    async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    connect_args = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool
else:
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

engine_kwargs["connect_args"] = connect_args

engine = create_async_engine(async_db_url, **engine_kwargs)

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
