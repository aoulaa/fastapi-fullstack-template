import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_client_cache_header(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    # Verify Cache-Control header is present and correct
    assert "cache-control" in response.headers
    expected_max_age = settings.CLIENT_CACHE_MAX_AGE
    assert f"max-age={expected_max_age}" in response.headers["cache-control"]
