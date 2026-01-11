from unittest.mock import AsyncMock, patch

import pytest

from app.core.health import check_database_health, check_redis_health


@pytest.mark.asyncio
async def test_check_database_health_success(db):
    # db is an AsyncSession
    # Mocking db.execute to succeed
    with patch.object(db, "execute", new_callable=AsyncMock) as mock_execute:
        result = await check_database_health(db)
        assert result is True
        mock_execute.assert_called_once()


@pytest.mark.asyncio
async def test_check_database_health_failure(db):
    with patch.object(db, "execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = Exception("DB Error")
        result = await check_database_health(db)
        assert result is False


@pytest.mark.asyncio
async def test_check_redis_health_success():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True

    result = await check_redis_health(mock_redis)
    assert result is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_check_redis_health_failure():
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = Exception("Redis Error")

    result = await check_redis_health(mock_redis)
    assert result is False
