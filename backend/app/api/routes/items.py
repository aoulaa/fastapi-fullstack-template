from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.crud.items import crud_items
from app.schemas.common import Message
from app.schemas.items import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic, operation_id="read_items")
async def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items.
    """
    if current_user.is_superuser:
        # Superusers can see all items
        result = await crud_items.get_multi(db=session, offset=skip, limit=limit, is_deleted=False)
    else:
        # Regular users can only see their own items
        result = await crud_items.get_multi(
            db=session, offset=skip, limit=limit, owner_id=current_user.id, is_deleted=False
        )

    # Convert SQLAlchemy models to Pydantic models
    items_data = [ItemPublic.model_validate(item) for item in result["data"]]
    return ItemsPublic(data=items_data, count=result["total_count"])


@router.get("/{id}", response_model=ItemPublic, operation_id="read_item")
async def read_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
) -> Any:
    """
    Get item by ID.
    """
    item = await crud_items.get(db=session, id=id, is_deleted=False)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return item


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED, operation_id="create_item")
async def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ItemCreate,
) -> Any:
    """
    Create new item.
    """
    item = await crud_items.create(db=session, item_create=item_in, owner_id=current_user.id)
    return item


@router.put("/{id}", response_model=ItemPublic, operation_id="update_item")
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = await crud_items.get(db=session, id=id, is_deleted=False)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    item = await crud_items.update(db=session, db_item=item, item_update=item_in)
    return item


@router.delete("/{id}", response_model=Message, operation_id="delete_item")
async def delete_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
) -> Message:
    """
    Delete an item.
    """
    item = await crud_items.get(db=session, id=id, is_deleted=False)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    await crud_items.delete(db=session, id=id)
    return Message(message="Item deleted successfully")
