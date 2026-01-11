import asyncio
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSession, local_session
from app.core.security import get_password_hash
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_first_user(session: AsyncSession) -> None:
    try:
        name = settings.ADMIN_NAME
        email = settings.ADMIN_EMAIL
        username = settings.ADMIN_USERNAME
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)

        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                name=name,
                email=email,
                username=username,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
            )
            session.add(user)
            await session.commit()
            logger.info(f"Admin user {username} created successfully.")
        else:
            logger.info(f"Admin user {username} already exists.")

    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating admin user: {e}")


async def main() -> None:
    async with local_session() as session:
        await create_first_user(session)


if __name__ == "__main__":
    asyncio.run(main())
