import pytest

from app.crud.users import crud_users
from app.schemas.users import UserCreate, UserUpdate
from tests.helpers.generators import create_user


@pytest.mark.asyncio
async def test_create_user(db):
    user_in = UserCreate(name="New User", username="newuser", email="new@example.com", password="Password123!")
    user = await crud_users.create(db, user_in)
    assert user.email == user_in.email
    assert user.id is not None
    assert user.hashed_password != user_in.password


@pytest.mark.asyncio
async def test_authenticate_user(db):
    email = "auth@example.com"
    password = "Password123!"
    user_in = UserCreate(name="Auth User", username="authuser", email=email, password=password)
    await crud_users.create(db, user_in)

    authenticated_user = await crud_users.authenticate(db, username_or_email=email, password=password)
    assert authenticated_user is not None
    assert authenticated_user.email == email

    wrong_password = await crud_users.authenticate(db, username_or_email=email, password="wrongpassword")
    assert wrong_password is None


@pytest.mark.asyncio
async def test_not_authenticate_user(db):
    user = await crud_users.authenticate(db, username_or_email="nonexistent@example.com", password="password")
    assert user is None


@pytest.mark.asyncio
async def test_update_user(db):
    user = await create_user(db)
    new_name = "Updated Name"
    user_update = UserUpdate(name=new_name)
    updated_user = await crud_users.update(db, db_user=user, user_update=user_update)
    assert updated_user.name == new_name
    assert updated_user.email == user.email
