from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blacklist import TokenBlacklist

from .base import BaseCRUD


class CRUDTokenBlacklist(BaseCRUD[TokenBlacklist]):
    """CRUD operations for TokenBlacklist model."""

    async def create(
        self,
        db: AsyncSession,
        token: str,
        expires_at: datetime,
    ) -> TokenBlacklist:
        """Add a token to the blacklist.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        token : str
            The JWT token to blacklist.
        expires_at : datetime
            When the token expires.

        Returns
        -------
        TokenBlacklist
            The created blacklist entry.
        """
        db_token = TokenBlacklist(token=token, expires_at=expires_at)
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)
        return db_token

    async def is_blacklisted(
        self,
        db: AsyncSession,
        token: str,
    ) -> bool:
        """Check if a token is blacklisted.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        token : str
            The JWT token to check.

        Returns
        -------
        bool
            True if the token is blacklisted, False otherwise.
        """
        return await self.exists(db, token=token)

    async def cleanup_expired(
        self,
        db: AsyncSession,
    ) -> int:
        """Remove expired tokens from the blacklist.

        This can be run periodically to clean up old tokens.

        Parameters
        ----------
        db : AsyncSession
            The database session.

        Returns
        -------
        int
            Number of tokens deleted.
        """
        from datetime import UTC, datetime

        from sqlalchemy import delete

        query = delete(TokenBlacklist).where(TokenBlacklist.expires_at < datetime.now(UTC))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount


# Create a singleton instance
crud_token_blacklist = CRUDTokenBlacklist(TokenBlacklist)
