from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logger import logging
from app.core.security import TokenType, verify_token
from app.crud import crud_users
from app.models.user import User

logger = logging.getLogger(__name__)

# --- Dependency Type Aliases for Cleaner Routes ---
SessionDep = Annotated[AsyncSession, Depends(async_get_db)]

# auto_error=False so missing Bearer doesn't immediately 401 — cookie auth is tried first
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token", auto_error=False)


async def get_current_user(
    request: Request,
    db: SessionDep,
    bearer_token: Annotated[str | None, Depends(_oauth2_scheme)] = None,
) -> User:
    # Prefer httpOnly cookie; fall back to Bearer token (for Swagger UI / API clients)
    token = request.cookies.get("access_token") or bearer_token
    if not token:
        raise UnauthorizedException("User not authenticated.")

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

    if user.token_version != token_data.token_version:
        raise UnauthorizedException("Token has been revoked.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise ForbiddenException("You do not have enough privileges.")
    return current_user


SuperUserDep = Annotated[User, Depends(get_current_superuser)]


async def get_optional_user(request: Request, db: SessionDep) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None

    try:
        token_data = await verify_token(token, TokenType.ACCESS, db)
        if token_data is None:
            return None

        if "@" in token_data.username_or_email:
            user = await crud_users.get_by_email(db=db, email=token_data.username_or_email, is_deleted=False)
        else:
            user = await crud_users.get_by_username(db=db, username=token_data.username_or_email, is_deleted=False)

        if not user or not user.is_active or user.token_version != token_data.token_version:
            return None

        return user
    except HTTPException:
        return None
    except Exception as exc:
        logger.error(f"Unexpected error in get_optional_user: {exc}")
        return None
