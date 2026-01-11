import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

# Monkeypatching the server_default for tests to be compatible with SQLite
# MappedColumn object is not directly mutable for server_default?
# It seems mapped_column returns a MappedColumn which we can access via .column usually in Declarative,
# but before mapper configuration it's just a descriptor/object.
# Actually, `TimestampMixin.created_at` in the class body is a `MappedColumn`.
# We need to modify its underlying Column definition or properly mock it.
# Let's try to modify the arguments directly if possible or re-declare.
# Easier way: iterate over models and fix them? No, they are already defined.
# We can try to replace the `server_default` on the Table object if it was created,
# but we are creating the engine dynamically.
# Let's try to just modify the MappedColumn params if possible.
# `mapped_column` returns a `MappedColumn` which stores args.
# It seems direct attribute access failed.
# Alternative: Define a compilation hook for SQLite to replace "current_timestamp(0)"
from sqlalchemy.schema import CreateColumn

from app.core.db import Base, async_get_db
from app.core.security import create_access_token
from app.core.utils.cache import async_get_redis
from app.main import app

# --- SQLite Compatibility Fixes ---
# SQLite doesn't support "current_timestamp(0)", it only supports "CURRENT_TIMESTAMP"


@compiles(CreateColumn, "sqlite")
def use_current_timestamp(element, compiler, **kw):
    text = compiler.visit_create_column(element, **kw)
    text = text.replace("current_timestamp(0)", "CURRENT_TIMESTAMP")
    return text


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
        # Cleanup
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession, mock_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[async_get_db] = lambda: db
    app.dependency_overrides[async_get_redis] = lambda: mock_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def mock_redis():
    """Mock Redis client globally for all tests."""
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.delete.return_value = True
    mock_redis_client.scan.return_value = (0, [])

    with (
        patch("app.core.utils.cache.client", mock_redis_client),
        patch("app.core.utils.rate_limit.rate_limiter.client", mock_redis_client),
    ):
        yield mock_redis_client


@pytest_asyncio.fixture
async def superuser_token_headers(db: AsyncSession) -> dict[str, str]:
    from tests.helpers.generators import create_user

    user = await create_user(db, is_superuser=True)
    access_token = await create_access_token(data={"sub": user.email, "token_type": "access"})
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def normal_user_token_headers(db: AsyncSession) -> dict[str, str]:
    from tests.helpers.generators import create_user

    user = await create_user(db, is_superuser=False)
    access_token = await create_access_token(data={"sub": user.email, "token_type": "access"})
    return {"Authorization": f"Bearer {access_token}"}
