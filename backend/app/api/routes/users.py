from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_current_user
from app.core.db import async_get_db
from app.core.exceptions import DuplicateValueException, ForbiddenException, NotFoundException
from app.core.security import blacklist_token, oauth2_scheme
from app.crud import crud_users
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(tags=["users"])


class PaginatedResponse(BaseModel):
    """Pagination response wrapper."""

    data: list[UserRead]
    total_count: int
    page: int
    items_per_page: int
    total_pages: int


@router.post("/user", response_model=UserRead, status_code=201)
async def write_user(
    request: Request, user: UserCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserRead:
    # Check for duplicates
    email_exists = await crud_users.exists(db=db, email=user.email)
    if email_exists:
        raise DuplicateValueException("Email is already registered")

    username_exists = await crud_users.exists(db=db, username=user.username)
    if username_exists:
        raise DuplicateValueException("Username not available")

    # Create user (password hashing handled in CRUD layer)
    created_user = await crud_users.create(db=db, user_create=user)

    # Convert to response schema
    return UserRead(**created_user.__dict__)


@router.get("/users", response_model=PaginatedResponse)
async def read_users(
    request: Request, db: Annotated[AsyncSession, Depends(async_get_db)], page: int = 1, items_per_page: int = 10
) -> PaginatedResponse:
    offset = (page - 1) * items_per_page
    result = await crud_users.get_multi(
        db=db,
        offset=offset,
        limit=items_per_page,
        is_deleted=False,
    )

    users = result["data"]
    total_count = result["total_count"]
    total_pages = (total_count + items_per_page - 1) // items_per_page

    return PaginatedResponse(
        data=[UserRead(**user.__dict__) for user in users],
        total_count=total_count,
        page=page,
        items_per_page=items_per_page,
        total_pages=total_pages,
    )


@router.get("/user/me/", response_model=UserRead)
async def read_users_me(request: Request, current_user: Annotated[dict, Depends(get_current_user)]) -> UserRead:
    return UserRead(**current_user)


@router.get("/user/{username}", response_model=UserRead)
async def read_user(request: Request, username: str, db: Annotated[AsyncSession, Depends(async_get_db)]) -> UserRead:
    db_user = await crud_users.get_by_username(db=db, username=username, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    return UserRead(**db_user.__dict__)


@router.patch("/user/{username}")
async def patch_user(
    request: Request,
    values: UserUpdate,
    username: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get_by_username(db=db, username=username)
    if db_user is None:
        raise NotFoundException("User not found")

    # Check authorization
    if db_user.username != current_user["username"]:
        raise ForbiddenException()

    # Check for duplicate email if changing
    if values.email is not None and values.email != db_user.email:
        if await crud_users.exists(db=db, email=values.email):
            raise DuplicateValueException("Email is already registered")

    # Check for duplicate username if changing
    if values.username is not None and values.username != db_user.username:
        if await crud_users.exists(db=db, username=values.username):
            raise DuplicateValueException("Username not available")

    # Update user
    await crud_users.update(db=db, db_user=db_user, user_update=values)
    return {"message": "User updated"}


@router.delete("/user/{username}")
async def erase_user(
    request: Request,
    username: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    db_user = await crud_users.get_by_username(db=db, username=username)
    if not db_user:
        raise NotFoundException("User not found")

    if username != current_user["username"]:
        raise ForbiddenException()

    await crud_users.delete(db=db, username=username)
    await blacklist_token(token=token, db=db)
    return {"message": "User deleted"}


@router.delete("/db_user/{username}", dependencies=[Depends(get_current_superuser)])
async def erase_db_user(
    request: Request,
    username: str,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    user_exists = await crud_users.exists(db=db, username=username)
    if not user_exists:
        raise NotFoundException("User not found")

    await crud_users.db_delete(db=db, username=username)
    await blacklist_token(token=token, db=db)
    return {"message": "User deleted from the database"}
