import pytest
from sqlalchemy.orm import selectinload

from app.crud.users import crud_users
from app.models.user import User
from tests.helpers.generators import create_user


@pytest.mark.asyncio
async def test_crud_get(db):
    user = await create_user(db)
    fetched_user = await crud_users.get(db, id=user.id)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email


@pytest.mark.asyncio
async def test_crud_get_with_options(db):
    user = await create_user(db)
    # Testing that options parameter is accepted and doesn't crash
    fetched_user = await crud_users.get(db, id=user.id, options=[selectinload(User.items)])
    assert fetched_user is not None
    assert fetched_user.id == user.id
    # Accessing items should not raise an error if selectinload worked
    assert isinstance(fetched_user.items, list)


@pytest.mark.asyncio
async def test_crud_get_not_found(db):
    fetched_user = await crud_users.get(db, id=999999)
    assert fetched_user is None


@pytest.mark.asyncio
async def test_crud_get_multi(db):
    await create_user(db)
    await create_user(db)
    result = await crud_users.get_multi(db, limit=10)
    assert len(result["data"]) >= 2
    assert result["total_count"] >= 2


@pytest.mark.asyncio
async def test_crud_get_multi_with_options(db):
    await create_user(db)
    # Testing that options parameter is accepted in get_multi
    result = await crud_users.get_multi(db, limit=10, options=[selectinload(User.items)])
    assert len(result["data"]) >= 1
    assert isinstance(result["data"][0].items, list)


@pytest.mark.asyncio
async def test_crud_exists(db):
    user = await create_user(db)
    exists = await crud_users.exists(db, id=user.id)
    assert exists is True

    not_exists = await crud_users.exists(db, id=999999)
    assert not_exists is False


@pytest.mark.asyncio
async def test_crud_count(db):
    initial_count = await crud_users.count(db)
    await create_user(db)
    new_count = await crud_users.count(db)
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_crud_delete(db):
    user = await create_user(db)
    deleted = await crud_users.delete(db, id=user.id)
    assert deleted is True

    # Check it is soft deleted
    fetched_user = await crud_users.get(db, id=user.id)
    assert fetched_user.is_deleted is True
    assert fetched_user.deleted_at is not None


@pytest.mark.asyncio
async def test_crud_db_delete(db):
    user = await create_user(db)
    deleted = await crud_users.db_delete(db, id=user.id)
    assert deleted is True

    # Check it is hard deleted
    fetched_user = await crud_users.get(db, id=user.id)
    assert fetched_user is None
