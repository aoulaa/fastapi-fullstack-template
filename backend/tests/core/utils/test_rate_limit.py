import pytest

from app.core.utils.rate_limit import rate_limiter


@pytest.mark.asyncio
async def test_rate_limiter_allow(mock_redis):
    mock_redis.incr.return_value = 1
    limited = await rate_limiter.is_rate_limited("test_key", 10, 60)
    assert limited is False


@pytest.mark.asyncio
async def test_rate_limiter_block(mock_redis):
    mock_redis.incr.return_value = 11
    limited = await rate_limiter.is_rate_limited("test_key", 10, 60)
    assert limited is True
