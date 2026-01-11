from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User

fake = Faker()


async def create_user(db: AsyncSession, is_superuser: bool = False, password: str = None, email: str = None) -> User:
    if not password:
        password = fake.password()
    if not email:
        email = fake.email()
    username = fake.user_name()

    user = User(
        name=fake.name(),
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        profile_image_url=fake.image_url(),
        is_active=True,
        is_superuser=is_superuser,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
