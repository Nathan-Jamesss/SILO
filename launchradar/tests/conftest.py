# tests/conftest.py — Shared pytest fixtures and helpers
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from models import Base


@pytest_asyncio.fixture
async def test_db() -> AsyncSession:
    """
    Provide an in-memory SQLite async session for each test.
    Tables are created fresh per test — no shared state between tests.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session

    await engine.dispose()


def make_test_record(**overrides) -> dict:
    """
    Build a valid opportunity dict for use in tests.
    Any field can be overridden via keyword arguments.

    Example:
        make_test_record(title="Custom Grant", source_url="https://example.com/x")
    """
    base = {
        "title":       "Test Startup Grant 2025",
        "type":        "Grant",
        "organizer":   "Test Foundation",
        "location":    "Remote",
        "deadline":    None,
        "description": "A test grant for automated testing.",
        "source_url":  "https://test.example.com/grant-1",
        "source_name": "TestSource",
    }
    base.update(overrides)
    return base
