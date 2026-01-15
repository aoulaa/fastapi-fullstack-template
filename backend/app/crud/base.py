from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseCRUD(Generic[ModelType]):
    """Base class for CRUD operations on SQLAlchemy models.

    Provides common database operations that can be inherited by
    model-specific CRUD classes.

    Requirements
    ------------
    Models MUST inherit from `app.models.base.BaseModel`, which guarantees:

    - **ID field**: `id: int` (primary key, auto-increment)
    - **Timestamps**: `created_at`, `updated_at` (automatic tracking)
    - **Soft Delete**: `is_deleted: bool`, `deleted_at: datetime | None`

    These fields enable the generic `delete()` and `db_delete()` methods
    to work correctly across all models.

    For Custom Models
    -----------------
    If you have a model that should NOT inherit from BaseModel:

    1. **Option A**: Inherit from BaseModel anyway (unused fields are okay)
    2. **Option B**: Create a custom CRUD class without extending BaseCRUD
    3. **Option C**: Override the `delete()` method in your model's CRUD class

    Type Parameters
    ---------------
    ModelType : BaseModel
        The SQLAlchemy model type this CRUD instance operates on.
        Must inherit from `app.models.base.BaseModel`.

    Examples
    --------
    Create a CRUD instance for your model:

    >>> from app.models.user import User
    >>> from app.crud.base import BaseCRUD
    >>>
    >>> class CRUDUser(BaseCRUD[User]):
    >>>     async def create(self, db, user_create):
    >>>         # Custom create logic here
    >>>         pass
    >>>
    >>> crud_users = CRUDUser(User)
    """

    def __init__(self, model: type[ModelType]):
        """Initialize the CRUD instance with a model.

        Parameters
        ----------
        model : type[ModelType]
            The SQLAlchemy model class to perform operations on.
        """
        self.model = model

    def _build_query(
        self,
        options: Sequence[Any] | None = None,
        **kwargs: Any,
    ) -> Select[tuple[ModelType]]:
        """Build the base query with optional loading options and filters."""
        query = select(self.model)
        if options:
            query = query.options(*options)
        for field, value in kwargs.items():
            query = query.where(getattr(self.model, field) == value)
        return query

    async def get(
        self,
        db: AsyncSession,
        options: Sequence[Any] | None = None,
        **kwargs: Any,
    ) -> ModelType | None:
        """Fetch a single record by any field.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        options : Sequence[Any] | None, default=None
            SQLAlchemy loading options (e.g., selectinload).
        **kwargs : Any
            Field-value pairs to filter by (e.g., email="user@example.com").

        Returns
        -------
        ModelType | None
            The matching record, or None if not found.

        Examples
        --------
        >>> from sqlalchemy.orm import selectinload
        >>> user = await crud.get(db, email="user@example.com", options=[selectinload(User.items)])
        >>> user = await crud.get(db, username="john", is_deleted=False)
        """
        query = self._build_query(options=options, **kwargs)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        options: Sequence[Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch multiple records with pagination.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        offset : int, default=0
            Number of records to skip.
        limit : int, default=100
            Maximum number of records to return.
        options : Sequence[Any] | None, default=None
            SQLAlchemy loading options (e.g., selectinload).
        **kwargs : Any
            Field-value pairs to filter by.

        Returns
        -------
        dict[str, Any]
            Dictionary containing 'data' (list of records) and 'total_count'.

        Examples
        --------
        >>> from sqlalchemy.orm import selectinload
        >>> result = await crud.get_multi(db, offset=0, limit=10, options=[selectinload(User.items)])
        >>> users = result['data']
        >>> total = result['total_count']
        """
        # Build the filtered query (without options for count)
        query = self._build_query(**kwargs)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        # Get paginated data with options
        data_query = query.offset(offset).limit(limit)
        if options:
            data_query = data_query.options(*options)
        result = await db.execute(data_query)
        data = result.scalars().all()

        return {"data": data, "total_count": total_count}

    async def exists(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> bool:
        """Check if a record exists.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        **kwargs : Any
            Field-value pairs to filter by.

        Returns
        -------
        bool
            True if a matching record exists, False otherwise.

        Examples
        --------
        >>> exists = await crud.exists(db, email="user@example.com")
        """
        query = self._build_query(**kwargs)

        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        count = result.scalar_one()
        return count > 0

    async def count(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> int:
        """Count records matching the filter.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        **kwargs : Any
            Field-value pairs to filter by.

        Returns
        -------
        int
            Number of matching records.
        """
        query = self._build_query(**kwargs)

        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        return result.scalar_one()

    async def delete(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> bool:
        """Soft delete a record (sets is_deleted=True, deleted_at=now).

        This method requires the model to inherit from BaseModel,
        which provides the soft-delete fields.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        **kwargs : Any
            Field-value pairs to identify the record to delete.

        Returns
        -------
        bool
            True if a record was deleted, False if not found.

        Notes
        -----
        This is a "soft delete" - the record remains in the database
        but is marked as deleted. Use `db_delete()` for permanent removal.

        Examples
        --------
        >>> deleted = await crud.delete(db, username="john")
        >>> # User still exists in DB but is_deleted=True
        """
        record = await self.get(db, **kwargs)
        if record is None:
            return False

        record.is_deleted = True
        record.deleted_at = datetime.now(UTC)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return True

    async def db_delete(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> bool:
        """Hard delete a record (removes from database).

        Parameters
        ----------
        db : AsyncSession
            The database session.
        **kwargs : Any
            Field-value pairs to identify the record to delete.

        Returns
        -------
        bool
            True if a record was deleted, False if not found.

        Examples
        --------
        >>> deleted = await crud.db_delete(db, id=123)
        """
        record = await self.get(db, **kwargs)
        if record is None:
            return False

        await db.delete(record)
        await db.commit()
        return True
