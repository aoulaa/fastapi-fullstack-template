import pytest

from app.models.user import User


@pytest.mark.asyncio
async def test_user_creation(db):
    user = User(
        name="Test User",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_secret",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.id is not None
    assert user.created_at is not None
    assert user.is_deleted is False


@pytest.mark.asyncio
async def test_soft_delete(db):
    user = User(
        name="Delete User",
        username="deleteuser",
        email="delete@example.com",
        hashed_password="hashed_secret",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user.is_deleted = True
    await db.commit()
    await db.refresh(user)

    assert user.is_deleted is True
