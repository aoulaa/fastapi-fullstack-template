from typing import Annotated

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logger import logging
from app.core.security import TokenType, oauth2_scheme, verify_token
from app.core.utils.cache import async_get_redis
from app.crud import crud_users
from app.models.user import User

logger = logging.getLogger(__name__)

# --- Dependency Type Aliases for Cleaner Routes ---
SessionDep = Annotated[AsyncSession, Depends(async_get_db)]
RedisDep = Annotated[Redis, Depends(async_get_redis)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep) -> User:
    token_data = await verify_token(token, TokenType.ACCESS, db)
    if token_data is None:
        raise UnauthorizedException("User not authenticated.")

    if "@" in token_data.username_or_email:
        user = await crud_users.get_by_email(db=db, email=token_data.username_or_email, is_deleted=False)
    else:
        user = await crud_users.get_by_username(db=db, username=token_data.username_or_email, is_deleted=False)

    if not user:
        raise UnauthorizedException("User not found.")

    if not user.is_active:
        raise UnauthorizedException("Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise ForbiddenException("You do not have enough privileges.")
    return current_user


SuperUserDep = Annotated[User, Depends(get_current_superuser)]


async def get_optional_user(request: Request, db: SessionDep) -> User | None:
    token = request.headers.get("Authorization")
    if not token:
        return None

    try:
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() != "bearer" or not token_value:
            return None

        return await get_current_user(token_value, db=db)
    except HTTPException:
        return None
    except Exception as exc:
        logger.error(f"Unexpected error in get_optional_user: {exc}")
        return None
