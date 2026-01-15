import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep, SuperUserDep
from app.core.exceptions import DuplicateValueException, ForbiddenException, NotFoundException
from app.core.security import get_password_hash, oauth2_scheme, verify_password
from app.crud import crud_users
from app.schemas.users import UpdatePassword, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


class PaginatedResponse(BaseModel):
    data: list[UserRead]
    count: int


@router.post("/", response_model=UserRead, status_code=201, operation_id="create_user")
async def write_user(
    request: Request,
    user: UserCreate,
    current_user: SuperUserDep,
    db: SessionDep,
) -> UserRead:
    """Create a new user with generated username if missing (Superuser only)."""
    email_exists = await crud_users.exists(db=db, email=user.email)
    if email_exists:
        raise DuplicateValueException("Email is already registered")

    if user.username:
        username_exists = await crud_users.exists(db=db, username=user.username)
        if username_exists:
            raise DuplicateValueException("Username not available")
    else:
        base_username = user.email.split("@")[0]
        base_username = re.sub(r"[^a-z0-9]", "", base_username.lower())
        username = base_username
        counter = 1
        while await crud_users.exists(db=db, username=username):
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username

    created_user = await crud_users.create(db=db, user_create=user)
    return UserRead.model_validate(created_user)


@router.get("/", response_model=PaginatedResponse, operation_id="read_users")
async def read_users(
    db: SessionDep,
    skip: int = 0,
    limit: int = 10,
) -> PaginatedResponse:
    """Retrieve users with pagination."""
    result = await crud_users.get_multi(
        db=db,
        offset=skip,
        limit=limit,
        is_deleted=False,
    )

    users = result["data"]
    total_count = result["total_count"]

    return PaginatedResponse(
        data=[UserRead.model_validate(user) for user in users],
        count=total_count,
    )


@router.get("/me", response_model=UserRead, operation_id="read_user_me")
async def read_users_me(current_user: CurrentUser) -> UserRead:
    """Get current user information."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, operation_id="update_user_me")
async def update_user_me(
    values: UserUpdate,
    current_user: CurrentUser,
    db: SessionDep,
) -> UserRead:
    """Update current user profile."""
    db_user = await crud_users.get(db=db, id=current_user.id)
    if db_user is None:
        raise NotFoundException("User not found")

    if values.email is not None and values.email != db_user.email:
        if await crud_users.exists(db=db, email=values.email):
            raise DuplicateValueException("Email is already registered")

    if values.username is not None and values.username != db_user.username:
        if await crud_users.exists(db=db, username=values.username):
            raise DuplicateValueException("Username not available")

    update_data = values.model_dump(exclude_unset=True)
    if not current_user.is_superuser:
        update_data.pop("is_superuser", None)
        update_data.pop("is_active", None)

    updated_user = await crud_users.update(db=db, db_user=db_user, user_update=update_data)
    return UserRead.model_validate(updated_user)


@router.patch("/me/password", response_model=dict[str, str], operation_id="update_password_me")
async def update_password_me(
    body: UpdatePassword,
    current_user: CurrentUser,
    db: SessionDep,
) -> dict[str, str]:
    """Update current user password."""
    if not await verify_password(body.current_password, current_user.hashed_password):
        raise ForbiddenException("Incorrect password")

    if body.current_password == body.new_password:
        raise DuplicateValueException("New password cannot be the same as the current password")

    hashed_password = get_password_hash(body.new_password)
    await crud_users.update(db=db, db_user=current_user, user_update={"hashed_password": hashed_password})
    return {"message": "Password updated successfully"}


@router.delete("/me", response_model=dict[str, str], operation_id="delete_user_me")
async def delete_user_me(
    current_user: CurrentUser,
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, str]:
    """Delete own user account."""
    if current_user.is_superuser:
        raise ForbiddenException(
            "Superusers cannot delete themselves. Please ask another admin to delete your account."
        )

    await crud_users.delete(db=db, id=current_user.id)
    return {"message": "User deleted successfully"}


@router.get("/{user_id}", response_model=UserRead, operation_id="read_user_by_id")
async def read_user_by_id(
    user_id: int,
    db: SessionDep,
) -> UserRead:
    """Get a specific user by ID."""
    db_user = await crud_users.get(db=db, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    return UserRead.model_validate(db_user)


@router.patch("/{user_id}", response_model=UserRead, operation_id="update_user")
async def patch_user(
    values: UserUpdate,
    user_id: int,
    current_user: CurrentUser,
    db: SessionDep,
) -> UserRead:
    """Update a specific user profile (Self or Superuser)."""
    db_user = await crud_users.get(db=db, id=user_id)
    if db_user is None:
        raise NotFoundException("User not found")

    if not current_user.is_superuser and db_user.id != current_user.id:
        raise ForbiddenException()

    if values.email is not None and values.email != db_user.email:
        if await crud_users.exists(db=db, email=values.email):
            raise DuplicateValueException("Email is already registered")

    if values.username is not None and values.username != db_user.username:
        if await crud_users.exists(db=db, username=values.username):
            raise DuplicateValueException("Username not available")

    update_data = values.model_dump(exclude_unset=True)
    if not current_user.is_superuser:
        update_data.pop("is_superuser", None)
        update_data.pop("is_active", None)

    updated_user = await crud_users.update(db=db, db_user=db_user, user_update=update_data)
    return UserRead.model_validate(updated_user)


@router.delete("/{user_id}", operation_id="delete_user")
async def erase_user(
    user_id: int,
    current_user: CurrentUser,
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, str]:
    """Delete a user profile (Self or Superuser)."""
    db_user = await crud_users.get(db=db, id=user_id)
    if not db_user:
        raise NotFoundException("User not found")

    if not current_user.is_superuser and user_id != current_user.id:
        raise ForbiddenException()

    await crud_users.delete(db=db, id=user_id)
    return {"message": "User deleted"}


@router.delete("/db_user/{username}", operation_id="delete_db_user")
async def erase_db_user(
    username: str,
    current_user: SuperUserDep,
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, str]:
    """Permanently delete a user from the database (Superuser only)."""
    user_exists = await crud_users.exists(db=db, username=username)
    if not user_exists:
        raise NotFoundException("User not found")

    await crud_users.db_delete(db=db, username=username)
    return {"message": "User deleted from the database"}
