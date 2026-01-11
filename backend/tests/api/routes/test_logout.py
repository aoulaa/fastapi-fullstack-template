import pytest
from httpx import AsyncClient

from app.core.security import create_refresh_token


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, db, normal_user_token_headers):
    # We need a refresh token in cookie
    # normal_user_token_headers contains access token.
    # We can create a refresh token manually.

    refresh_token = await create_refresh_token(data={"sub": "test@example.com"})

    client.cookies.set("refresh_token", refresh_token)

    response = await client.post("/api/v1/logout", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    assert "refresh_token" not in response.cookies or response.cookies["refresh_token"] == ""
    # httpx client might handle delete cookie by removing it or setting it to empty.
    # Response usually sets Set-Cookie: refresh_token=""; expires=...


@pytest.mark.asyncio
async def test_logout_no_refresh_token(client: AsyncClient, normal_user_token_headers):
    response = await client.post("/api/v1/logout", headers=normal_user_token_headers)
    assert response.status_code == 401  # UnauthorizedException("Refresh token not found")
