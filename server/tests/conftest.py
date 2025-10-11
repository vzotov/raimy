"""
Test fixtures and configuration for pytest
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql+asyncpg://raimy_user:raimy_password@localhost:5432/raimy_test"
os.environ["AUTH_SERVICE_URL"] = "http://localhost:8001"
os.environ["API_URL"] = "http://localhost:8000"
os.environ["MCP_SERVER_URL"] = "http://localhost:8002/mcp"

import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import Base
from app.models import User, MealPlannerSession


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    """Create a test user"""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/pic.jpg"
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_session(test_db_session: AsyncSession, test_user: User):
    """Create a test meal planner session"""
    from uuid import uuid4

    session_id = uuid4()
    session = MealPlannerSession(
        id=session_id,
        user_id=test_user.email,
        session_name="Test Session",
        room_name=f"meal-planner-{session_id}",
        messages=[]
    )
    test_db_session.add(session)
    await test_db_session.commit()
    await test_db_session.refresh(session)
    return session
