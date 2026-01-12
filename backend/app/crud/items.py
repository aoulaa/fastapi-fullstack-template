from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.schemas.items import ItemCreate, ItemUpdate

from .base import BaseCRUD


class CRUDItem(BaseCRUD[Item]):
    """CRUD operations for Item model."""

    async def create(
        self,
        db: AsyncSession,
        item_create: ItemCreate,
        owner_id: int,
    ) -> Item:
        """Create a new item.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        item_create : ItemCreate
            Item creation data.
        owner_id : int
            ID of the user who owns this item.

        Returns
        -------
        Item
            The created item instance.
        """
        item_data = item_create.model_dump()
        db_item = Item(**item_data, owner_id=owner_id)

        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    async def update(
        self,
        db: AsyncSession,
        db_item: Item,
        item_update: ItemUpdate,
    ) -> Item:
        """Update an item.

        Parameters
        ----------
        db : AsyncSession
            The database session.
        db_item : Item
            The existing item instance to update.
        item_update : ItemUpdate
            Fields to update (only provided fields will be updated).

        Returns
        -------
        Item
            The updated item instance.
        """
        update_data = item_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_item, field, value)

        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item


crud_items = CRUDItem(Item)
