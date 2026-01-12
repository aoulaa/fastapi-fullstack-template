import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.item import Item


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, normal_user_token_headers):
    """Test creating a new item"""
    data = {
        "title": "Test Item",
        "description": "This is a test item",
    }
    response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


@pytest.mark.asyncio
async def test_create_item_without_description(client: AsyncClient, normal_user_token_headers):
    """Test creating an item with only title (description optional)"""
    data = {
        "title": "Minimal Item",
    }
    response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] is None or content["description"] == ""


@pytest.mark.asyncio
async def test_create_item_missing_title_fails(client: AsyncClient, normal_user_token_headers):
    """Test that creating item without title fails"""
    data = {
        "description": "No title",
    }
    response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_items(client: AsyncClient, normal_user_token_headers, db):
    """Test reading user's own items"""
    # Create a few items first
    for i in range(3):
        data = {
            "title": f"Test Item {i}",
            "description": f"Description {i}",
        }
        await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)

    # Read items
    response = await client.get("/api/v1/items/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert len(content["data"]) >= 3
    assert content["count"] >= 3


@pytest.mark.asyncio
async def test_read_items_pagination(client: AsyncClient, normal_user_token_headers):
    """Test items pagination"""
    # Create items
    for i in range(5):
        data = {"title": f"Item {i}"}
        await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)

    # Test pagination
    response = await client.get("/api/v1/items/?skip=0&limit=2", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) <= 2


@pytest.mark.asyncio
async def test_read_item_by_id(client: AsyncClient, normal_user_token_headers):
    """Test reading a single item by ID"""
    # Create item
    data = {
        "title": "Specific Item",
        "description": "Very specific",
    }
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Read it back
    response = await client.get(f"/api/v1/items/{item_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == item_id
    assert content["title"] == data["title"]


@pytest.mark.asyncio
async def test_read_nonexistent_item_fails(client: AsyncClient, normal_user_token_headers):
    """Test reading non-existent item returns 404"""
    response = await client.get("/api/v1/items/999999", headers=normal_user_token_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient, normal_user_token_headers):
    """Test updating an item"""
    # Create item
    data = {"title": "Original Title", "description": "Original description"}
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Update it
    update_data = {"title": "Updated Title", "description": "Updated description"}
    response = await client.put(f"/api/v1/items/{item_id}", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_update_item_partial(client: AsyncClient, normal_user_token_headers):
    """Test partially updating an item (only title)"""
    # Create item
    data = {"title": "Original", "description": "Keep this"}
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Update only title
    update_data = {"title": "New Title"}
    response = await client.put(f"/api/v1/items/{item_id}", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, normal_user_token_headers, db):
    """Test deleting an item"""
    # Create item
    data = {"title": "To Delete"}
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/v1/items/{item_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert "message" in response.json()

    # Verify it's soft deleted
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    db_item = result.scalar_one_or_none()
    assert db_item is not None
    assert db_item.is_deleted is True


@pytest.mark.asyncio
async def test_normal_user_cannot_see_others_items(client: AsyncClient, superuser_token_headers, db):
    """Test that normal users can only see their own items"""
    from app.core.security import create_access_token
    from tests.helpers.generators import create_user

    # Create two users
    user1 = await create_user(db, email="user1@example.com")
    user2 = await create_user(db, email="user2@example.com")

    token1 = await create_access_token(data={"sub": user1.email, "token_type": "access"})
    token2 = await create_access_token(data={"sub": user2.email, "token_type": "access"})
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User1 creates an item
    data = {"title": "User1's Item"}
    create_response = await client.post("/api/v1/items/", json=data, headers=headers1)
    item_id = create_response.json()["id"]

    # User2 tries to access User1's item
    response = await client.get(f"/api/v1/items/{item_id}", headers=headers2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_normal_user_cannot_update_others_items(client: AsyncClient, db):
    """Test that normal users cannot update others' items"""
    from app.core.security import create_access_token
    from tests.helpers.generators import create_user

    # Create two users
    user1 = await create_user(db, email="owner@example.com")
    user2 = await create_user(db, email="intruder@example.com")

    token1 = await create_access_token(data={"sub": user1.email, "token_type": "access"})
    token2 = await create_access_token(data={"sub": user2.email, "token_type": "access"})
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User1 creates an item
    data = {"title": "Owner's Item"}
    create_response = await client.post("/api/v1/items/", json=data, headers=headers1)
    item_id = create_response.json()["id"]

    # User2 tries to update User1's item
    update_data = {"title": "Hacked!"}
    response = await client.put(f"/api/v1/items/{item_id}", json=update_data, headers=headers2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_normal_user_cannot_delete_others_items(client: AsyncClient, db):
    """Test that normal users cannot delete others' items"""
    from app.core.security import create_access_token
    from tests.helpers.generators import create_user

    # Create two users
    user1 = await create_user(db, email="itemowner@example.com")
    user2 = await create_user(db, email="deleter@example.com")

    token1 = await create_access_token(data={"sub": user1.email, "token_type": "access"})
    token2 = await create_access_token(data={"sub": user2.email, "token_type": "access"})
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User1 creates an item
    data = {"title": "Protected Item"}
    create_response = await client.post("/api/v1/items/", json=data, headers=headers1)
    item_id = create_response.json()["id"]

    # User2 tries to delete User1's item
    response = await client.delete(f"/api/v1/items/{item_id}", headers=headers2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superuser_can_see_all_items(client: AsyncClient, superuser_token_headers, normal_user_token_headers):
    """Test that superusers can see all items"""
    # Normal user creates items
    for i in range(3):
        data = {"title": f"Normal User Item {i}"}
        await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)

    # Superuser should see all items
    response = await client.get("/api/v1/items/", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] >= 3


@pytest.mark.asyncio
async def test_superuser_can_update_any_item(client: AsyncClient, superuser_token_headers, normal_user_token_headers):
    """Test that superusers can update any item"""
    # Normal user creates an item
    data = {"title": "Normal Item"}
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Superuser updates it
    update_data = {"title": "Admin Updated"}
    response = await client.put(f"/api/v1/items/{item_id}", json=update_data, headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["title"] == update_data["title"]


@pytest.mark.asyncio
async def test_superuser_can_delete_any_item(client: AsyncClient, superuser_token_headers, normal_user_token_headers):
    """Test that superusers can delete any item"""
    # Normal user creates an item
    data = {"title": "To Be Admin Deleted"}
    create_response = await client.post("/api/v1/items/", json=data, headers=normal_user_token_headers)
    item_id = create_response.json()["id"]

    # Superuser deletes it
    response = await client.delete(f"/api/v1/items/{item_id}", headers=superuser_token_headers)
    assert response.status_code == 200
