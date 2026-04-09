from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TokenType,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.crud import crud_users
from app.schemas.auth import Token

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/access-token", response_model=Token, operation_id="login_access_token")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    user = await crud_users.authenticate(db=db, username_or_email=form_data.username, password=form_data.password)
    if not user:
        raise UnauthorizedException("Wrong username, email or password.")
    if not user.is_active:
        raise UnauthorizedException("Inactive user")

    token_payload = {"sub": user.username, "token_version": user.token_version}
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data=token_payload, expires_delta=access_token_expires)

    refresh_token = await create_refresh_token(data=token_payload)
    access_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=access_max_age
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=refresh_max_age
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", operation_id="refresh_access_token")
async def refresh_access_token(
    request: Request, response: Response, db: AsyncSession = Depends(async_get_db)
) -> dict[str, str]:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing.")

    token_data = await verify_token(refresh_token, TokenType.REFRESH, db)
    if not token_data:
        raise UnauthorizedException("Invalid refresh token.")

    # Look up user to verify token_version hasn't been incremented (e.g., after logout)
    if "@" in token_data.username_or_email:
        user = await crud_users.get_by_email(db=db, email=token_data.username_or_email, is_deleted=False)
    else:
        user = await crud_users.get_by_username(db=db, username=token_data.username_or_email, is_deleted=False)

    if not user or user.token_version != token_data.token_version:
        raise UnauthorizedException("Token has been revoked.")

    new_access_token = await create_access_token(data={"sub": user.username, "token_version": user.token_version})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
