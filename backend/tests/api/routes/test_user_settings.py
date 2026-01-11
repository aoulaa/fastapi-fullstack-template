import pytest
from httpx import AsyncClient

from app.core.security import verify_password
from app.crud.users import crud_users
from app.schemas.users import UserCreate


# Test Change Password
@pytest.mark.asyncio
async def test_update_password_me(client: AsyncClient, normal_user_token_headers: dict[str, str], db):
    # This test is just a placeholder/template, we are using the detailed ones below.
    pass


@pytest.mark.asyncio
async def test_user_change_password_success(client: AsyncClient, db):
    # Create user
    email = "changepassword@example.com"
    password = "OldPassword123!"
    user_in = UserCreate(email=email, password=password, name="Test User", username="changepass")
    user = await crud_users.create(db, user_in)

    # Login to get token
    login_data = {"username": email, "password": password}
    r_login = await client.post("/api/v1/login/access-token", data=login_data)
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    new_password = "NewPassword123!"
    r_update = await client.patch(
        "/api/v1/users/me/password", headers=headers, json={"current_password": password, "new_password": new_password}
    )
    assert r_update.status_code == 200

    # Verify DB update
    await db.refresh(user)
    assert await verify_password(new_password, user.hashed_password)

    # Verify old password login fails
    r_fail = await client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    assert r_fail.status_code == 401

    # Verify new password login succeeds
    r_success = await client.post("/api/v1/login/access-token", data={"username": email, "password": new_password})
    assert r_success.status_code == 200


@pytest.mark.asyncio
async def test_user_change_password_wrong_current(client: AsyncClient, db):
    # Create user
    email = "wrongcurrent@example.com"
    password = "Password123!"
    user_in = UserCreate(email=email, password=password, name="Test User", username="wrongcurrent")
    await crud_users.create(db, user_in)

    # Login
    r_login = await client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to change with wrong current password
    r_update = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "WrongPassword!", "new_password": "NewPassword123!"},
    )
    assert r_update.status_code == 403
    assert r_update.json()["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_user_change_password_same_password(client: AsyncClient, db):
    # Create user
    email = "samepass@example.com"
    password = "Password123!"
    user_in = UserCreate(email=email, password=password, name="Test User", username="samepass")
    await crud_users.create(db, user_in)

    # Login
    r_login = await client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to change with same password
    r_update = await client.patch(
        "/api/v1/users/me/password", headers=headers, json={"current_password": password, "new_password": password}
    )
    assert r_update.status_code == 409
    assert r_update.json()["detail"] == "New password cannot be the same as the current password"


@pytest.mark.asyncio
async def test_delete_user_me(client: AsyncClient, db):
    # Create user
    email = "deleteme@example.com"
    password = "Password123!"
    user_in = UserCreate(email=email, password=password, name="Tmp User", username="deleteme")
    user = await crud_users.create(db, user_in)
    user_id = user.id

    # Login
    r_login = await client.post("/api/v1/login/access-token", data={"username": email, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete Account
    r_delete = await client.delete("/api/v1/users/me", headers=headers)
    assert r_delete.status_code == 200
    assert r_delete.json()["message"] == "User deleted successfully"

    # Verify user is gone
    # Verify user is marked deleted
    user_in_db = await crud_users.get(db, id=user_id)
    assert user_in_db is not None
    assert user_in_db.is_deleted is True
    assert user_in_db.deleted_at is not None
