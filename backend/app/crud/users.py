from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate

from .base import BaseCRUD


class CRUDUser(BaseCRUD[User]):
    """CRUD operations for User model with authentication logic."""

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
        is_deleted: bool = False,
    ) -> User | None:
        """Get user by email address.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        email : str
            Email address to search for.
        is_deleted : bool, default=False
            Whether to include deleted users.

        Returns
        -------
        User | None
            The user if found, None otherwise.
        """
        return await self.get(db, email=email, is_deleted=is_deleted)

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str,
        is_deleted: bool = False,
    ) -> User | None:
        """Get user by username.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        username : str
            Username to search for.
        is_deleted : bool, default=False
            Whether to include deleted users.

        Returns
        -------
        User | None
            The user if found, None otherwise.
        """
        return await self.get(db, username=username, is_deleted=is_deleted)

    async def create(
        self,
        db: AsyncSession,
        user_create: UserCreate,
    ) -> User:
        """Create a new user with hashed password.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        user_create : UserCreate
            User creation data including plain password.

        Returns
        -------
        User
            The created user instance.

        Raises
        ------
        Exception
            If email or username already exists (handle in route layer).
        """
        hashed_password = get_password_hash(user_create.password)

        user_data = user_create.model_dump(exclude={"password", "name"})
        db_user = User(**user_data, hashed_password=hashed_password, name=user_create.name)

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update(
        self,
        db: AsyncSession,
        db_user: User,
        user_update: UserUpdate | dict[str, Any],
    ) -> User:
        """Update user information.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        db_user : User
            The existing user instance to update.
        user_update : UserUpdate | dict
            Fields to update (only provided fields will be updated).

        Returns
        -------
        User
            The updated user instance.
        """
        if isinstance(user_update, dict):
            update_data = user_update
        else:
            update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def authenticate(
        self,
        db: AsyncSession,
        username_or_email: str,
        password: str,
    ) -> User | None:
        """Authenticate a user by username/email and password.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        username_or_email : str
            Username or email address.
        password : str
            Plain text password to verify.

        Returns
        -------
        User | None
            The user if authentication succeeds, None otherwise.
        """
        if "@" in username_or_email:
            db_user = await self.get_by_email(db, email=username_or_email)
        else:
            db_user = await self.get_by_username(db, username=username_or_email)

        if db_user is None:
            return None

        if not await verify_password(password, db_user.hashed_password):
            return None

        return db_user


crud_users = CRUDUser(User)
