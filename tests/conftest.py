"""Shared test fixtures for all tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient
import os
from dotenv import load_dotenv

from core.database import Base, init_db, close_db, get_session

load_dotenv()

# Use test database (fallback to main DATABASE_URL if TEST_DATABASE_URL not set)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine):
    """Create test database session."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client_with_db(session):
    """Create test HTTP client with database dependency override."""
    from interface.api.main import app
    
    # Override the get_session dependency to use test session
    async def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()

