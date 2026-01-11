import pytest
from httpx import AsyncClient

from tests.helpers.generators import create_user


@pytest.mark.asyncio
async def test_get_access_token(client: AsyncClient, db):
    password = "password123"
    email = "login@example.com"
    await create_user(db, password=password, email=email)

    login_data = {"username": email, "password": password}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert "refresh_token" not in tokens  # Should be in cookie
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_incorrect_login(client: AsyncClient):
    login_data = {"username": "wrong@example.com", "password": "wrongpassword"}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong username, email or password."


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db):
    password = "password123"
    email = "refresh@example.com"
    await create_user(db, password=password, email=email)

    # Login to get refresh token
    login_data = {"username": email, "password": password}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    refresh_token = response.cookies["refresh_token"]

    # Use refresh token
    client.cookies.set("refresh_token", refresh_token)
    response_refresh = await client.post("/api/v1/login/refresh")
    assert response_refresh.status_code == 200
    assert "access_token" in response_refresh.json()
