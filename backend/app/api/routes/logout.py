from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.api.deps import CurrentUser, SessionDep
from app.core.exceptions import UnauthorizedException
from app.crud import crud_users

router = APIRouter(tags=["login"])


@router.post("/logout", operation_id="logout")
async def logout(
    response: Response,
    db: SessionDep,
    current_user: CurrentUser,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> dict[str, str]:
    """Logout user and invalidate all outstanding tokens."""
    if not refresh_token:
        raise UnauthorizedException("Refresh token not found")

    # Incrementing token_version makes all currently issued tokens invalid
    await crud_users.increment_token_version(db=db, user=current_user)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Logged out successfully"}
