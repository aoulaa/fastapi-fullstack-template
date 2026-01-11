import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient, mock_redis):
    # Determine the status of the redis dependency
    mock_redis.ping.return_value = True

    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "healthy"
    assert data["redis"] == "healthy"
