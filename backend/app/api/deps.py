from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logger import logging
from app.core.security import TokenType, oauth2_scheme, verify_token
from app.crud import crud_users

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = settings.DEFAULT_RATE_LIMIT_LIMIT
DEFAULT_PERIOD = settings.DEFAULT_RATE_LIMIT_PERIOD


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, Any]:
    token_data = await verify_token(token, TokenType.ACCESS, db)
    if token_data is None:
        raise UnauthorizedException("User not authenticated.")

    # Fetch user by email or username
    if "@" in token_data.username_or_email:
        user = await crud_users.get_by_email(db=db, email=token_data.username_or_email, is_deleted=False)
    else:
        user = await crud_users.get_by_username(db=db, username=token_data.username_or_email, is_deleted=False)

    if user:
        # Convert User instance to dict for compatibility with existing routes
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "profile_image_url": user.profile_image_url,
            "is_superuser": user.is_superuser,
            "hashed_password": user.hashed_password,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "is_deleted": user.is_deleted,
            "deleted_at": user.deleted_at,
        }

    raise UnauthorizedException("User not authenticated.")


async def get_optional_user(request: Request, db: AsyncSession = Depends(async_get_db)) -> dict | None:
    token = request.headers.get("Authorization")
    if not token:
        return None

    try:
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() != "bearer" or not token_value:
            return None

        token_data = await verify_token(token_value, TokenType.ACCESS, db)
        if token_data is None:
            return None

        return await get_current_user(token_value, db=db)

    except HTTPException as http_exc:
        if http_exc.status_code != 401:
            logger.error(f"Unexpected HTTPException in get_optional_user: {http_exc.detail}")
        return None

    except Exception as exc:
        logger.error(f"Unexpected error in get_optional_user: {exc}")
        return None


async def get_current_superuser(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not current_user["is_superuser"]:
        raise ForbiddenException("You do not have enough privileges.")

    return current_user
