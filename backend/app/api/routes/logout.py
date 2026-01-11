from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, Depends, Response

from app.api.deps import SessionDep
from app.core.exceptions import UnauthorizedException
from app.core.security import blacklist_tokens, oauth2_scheme

router = APIRouter(tags=["login"])


@router.post("/logout")
async def logout(
    response: Response,
    db: SessionDep,
    access_token: Annotated[str, Depends(oauth2_scheme)],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> dict[str, str]:
    """Logout user and blacklist tokens."""
    try:
        if not refresh_token:
            raise UnauthorizedException("Refresh token not found")

        await blacklist_tokens(access_token=access_token, refresh_token=refresh_token, db=db)
        response.delete_cookie(key="refresh_token")

        return {"message": "Logged out successfully"}

    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid token.")
