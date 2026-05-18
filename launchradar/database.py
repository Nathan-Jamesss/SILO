# database.py — async DB engine, session factory, and table init
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from models import Base
from config import settings

# Create the async engine (echo=False in production)
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

# Session factory — expire_on_commit=False prevents lazy-load errors after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    """Create all database tables on first run (idempotent) and auto-heal schema."""
    # 1. Create tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Check for and add any missing columns in 'opportunities' (SQLite self-healing migration)
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(opportunities)"))
        columns = [row[1] for row in result.all()]

        missing_cols = {
            "prize_pool": "REAL DEFAULT 0.0",
            "prize_pool_display": "TEXT",
            "num_applicants": "INTEGER DEFAULT 0",
            "is_hackathon": "INTEGER DEFAULT 1",
            "sector": "TEXT DEFAULT 'General'",
        }

        for col, col_type in missing_cols.items():
            if col not in columns:
                try:
                    await conn.execute(text(f"ALTER TABLE opportunities ADD COLUMN {col} {col_type}"))
                except Exception:
                    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an async DB session.

    Usage:
        session: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
