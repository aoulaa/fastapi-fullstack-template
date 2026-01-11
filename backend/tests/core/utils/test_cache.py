import json
from unittest.mock import AsyncMock

import pytest
from fastapi import Request

from app.core.utils.cache import cache


@pytest.mark.asyncio
async def test_cache_decorator_get_hit(mock_redis):
    # Setup mock to return cached data
    mock_redis.get.return_value = json.dumps({"data": "cached"}).encode()

    @cache(key_prefix="test_cache")
    async def sample_endpoint(request: Request, id: int):
        return {"data": "fresh"}

    request = AsyncMock(spec=Request)
    request.method = "GET"

    result = await sample_endpoint(request=request, id=1)

    assert result == {"data": "cached"}
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_cache_decorator_get_miss(mock_redis):
    mock_redis.get.return_value = None

    @cache(key_prefix="test_cache_miss")
    async def sample_endpoint(request: Request, id: int):
        return {"data": "fresh"}

    request = AsyncMock(spec=Request)
    request.method = "GET"

    result = await sample_endpoint(request=request, id=1)

    assert result == {"data": "fresh"}
    mock_redis.set.assert_called_once()
