import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, superuser_token_headers):
    data = {
        "email": "testcreate@example.com",
        "password": "Password123!",
        "name": "Test Create",
        "username": "testcreate",
    }
    # Trying with superuser headers because the route seems protected in app code
    response = await client.post("/api/v1/user", json=data, headers=superuser_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert "id" in content


@pytest.mark.asyncio
async def test_read_users_me(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v1/user/me/", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert "email" in response.json()


@pytest.mark.asyncio
async def test_read_user_by_username(client: AsyncClient, normal_user_token_headers, db):
    # normal_user_token_headers creates a user, let's use that one or create another.
    # We need the username of the logged in user or any user.
    # The fixture creates a user, but we don't have reference to it easily unless we query DB.
    # We can use /user/me to get username
    me_response = await client.get("/api/v1/user/me/", headers=normal_user_token_headers)
    username = me_response.json()["username"]

    response = await client.get(f"/api/v1/user/{username}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["username"] == username


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, normal_user_token_headers):
    me = await client.get("/api/v1/user/me/", headers=normal_user_token_headers)
    username = me.json()["username"]

    update_data = {"name": "Updated Name"}
    response = await client.patch(f"/api/v1/user/{username}", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 200

    # Verify update
    me_after = await client.get("/api/v1/user/me/", headers=normal_user_token_headers)
    assert me_after.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, db):
    # Need a fresh user for deletion test
    from app.core.security import create_access_token
    from tests.helpers.generators import create_user

    user = await create_user(db, email="todelete@example.com")
    token = await create_access_token(data={"sub": user.email, "token_type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/user/{user.username}", headers=headers)
    assert response.status_code == 200

    # Verify deleted
    # Depending on implementation, it might soft delete.
    # API usually returns 404 if deleted, or handles it.
    # Let's check crud directly or API 404
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    assert db_user.is_deleted is True
