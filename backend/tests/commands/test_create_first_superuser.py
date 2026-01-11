import pytest
from sqlalchemy import select

from app.commands.create_first_superuser import create_first_user
from app.core.config import settings
from app.models.user import User


@pytest.mark.asyncio
async def test_create_first_superuser(db):
    # Ensure no admin exists first
    stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()

    await create_first_user(db)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.is_superuser is True
    assert user.email == settings.ADMIN_EMAIL


@pytest.mark.asyncio
async def test_create_first_superuser_idempotency(db):
    await create_first_user(db)
    await create_first_user(db)  # Should not fail or create duplicate

    stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
    result = await db.execute(stmt)
    users = result.scalars().all()

    assert len(users) == 1
