"""
Tests for Items API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_item_with_stores(client: TestClient, sample_store: dict):
    """Test creating an item with store associations."""
    response = client.post("/api/items", json={
        "name": "Butter",
        "default_quantity": "1 lb",
        "quantity_is_int": False,
        "section": "Dairy",
        "store_ids": [sample_store["id"]]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Butter"
    assert data["section"] == "Dairy"
    assert len(data["stores"]) == 1
    assert data["stores"][0]["id"] == sample_store["id"]


def test_create_item_no_stores(client: TestClient):
    """Test creating an item with no specific stores."""
    response = client.post("/api/items", json={
        "name": "Rice",
        "default_quantity": "1 lb",
        "quantity_is_int": False,
        "section": "Other",
        "store_ids": []
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rice"
    assert len(data["stores"]) == 0


def test_create_item_duplicate_name(client: TestClient, sample_item: dict):
    """Test creating an item with duplicate name fails."""
    response = client.post("/api/items", json={
        "name": sample_item["name"],
        "store_ids": []
    })

    assert response.status_code == 409


def test_create_item_invalid_store(client: TestClient):
    """Test creating an item with invalid store ID fails."""
    response = client.post("/api/items", json={
        "name": "Invalid Item",
        "store_ids": [99999]
    })

    assert response.status_code == 404
    assert "Store" in response.json()["detail"]


def test_list_items(client: TestClient, sample_item: dict):
    """Test listing all items."""
    # Create another item
    client.post("/api/items", json={
        "name": "Another Item",
        "store_ids": []
    })

    response = client.get("/api/items")

    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 2


def test_list_items_filter_by_store(client: TestClient):
    """Test filtering items by store."""
    # Create stores
    store1 = client.post("/api/stores", json={"name": "Store1"}).json()
    store2 = client.post("/api/stores", json={"name": "Store2"}).json()

    # Create items
    item1 = client.post("/api/items", json={
        "name": "Item1",
        "store_ids": [store1["id"]]
    }).json()

    item2 = client.post("/api/items", json={
        "name": "Item2",
        "store_ids": [store2["id"]]
    }).json()

    item3 = client.post("/api/items", json={
        "name": "Item3",
        "store_ids": []  # No specific store
    }).json()

    # Filter by store1
    response = client.get(f"/api/items?store_id={store1['id']}")

    assert response.status_code == 200
    items = response.json()
    item_names = [i["name"] for i in items]
    assert "Item1" in item_names
    assert "Item3" in item_names  # Unspecified items included
    assert "Item2" not in item_names


def test_list_items_filter_by_section(client: TestClient):
    """Test filtering items by section."""
    client.post("/api/items", json={
        "name": "Dairy Item",
        "section": "Dairy",
        "store_ids": []
    })

    client.post("/api/items", json={
        "name": "Meat Item",
        "section": "Meat",
        "store_ids": []
    })

    response = client.get("/api/items?section=Dairy")

    assert response.status_code == 200
    items = response.json()
    assert all(i["section"] == "Dairy" for i in items)


def test_get_item(client: TestClient, sample_item: dict):
    """Test getting a single item by ID."""
    response = client.get(f"/api/items/{sample_item['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_item["id"]
    assert data["name"] == sample_item["name"]


def test_get_nonexistent_item(client: TestClient):
    """Test getting an item that doesn't exist."""
    response = client.get("/api/items/99999")

    assert response.status_code == 404


def test_update_item_name(client: TestClient, sample_item: dict):
    """Test updating an item's name."""
    response = client.put(
        f"/api/items/{sample_item['id']}",
        json={"name": "Updated Item"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Item"


def test_update_item_stores(client: TestClient, sample_item: dict):
    """Test updating an item's store associations."""
    # Create a new store
    new_store = client.post("/api/stores", json={"name": "NewStore"}).json()

    response = client.put(
        f"/api/items/{sample_item['id']}",
        json={"store_ids": [new_store["id"]]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["stores"]) == 1
    assert data["stores"][0]["id"] == new_store["id"]


def test_update_item_clear_stores(client: TestClient, sample_item: dict):
    """Test clearing an item's store associations."""
    response = client.put(
        f"/api/items/{sample_item['id']}",
        json={"store_ids": []}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["stores"]) == 0


def test_update_item_duplicate_name(client: TestClient):
    """Test updating an item to a duplicate name fails."""
    item1 = client.post("/api/items", json={
        "name": "Item1",
        "store_ids": []
    }).json()

    item2 = client.post("/api/items", json={
        "name": "Item2",
        "store_ids": []
    }).json()

    response = client.put(
        f"/api/items/{item1['id']}",
        json={"name": "Item2"}
    )

    assert response.status_code == 409


def test_delete_item(client: TestClient, sample_item: dict):
    """Test deleting an item."""
    response = client.delete(f"/api/items/{sample_item['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/items/{sample_item['id']}")
    assert response.status_code == 404


def test_delete_item_cascades_to_grocery_items(
    client: TestClient,
    sample_item: dict,
    sample_user: dict
):
    """Test that deleting an item cascades to grocery items."""
    # Create a grocery item referencing this item
    client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"]
    })

    # Delete the item - should succeed and cascade
    response = client.delete(f"/api/items/{sample_item['id']}")

    assert response.status_code == 204


def test_quantity_is_int_field(client: TestClient):
    """Test the quantity_is_int field works correctly."""
    # Create item with integer quantity
    int_item = client.post("/api/items", json={
        "name": "Apples",
        "default_quantity": "6",
        "quantity_is_int": True,
        "store_ids": []
    }).json()

    assert int_item["quantity_is_int"] is True

    # Create item with non-integer quantity
    non_int_item = client.post("/api/items", json={
        "name": "Milk",
        "default_quantity": "1 gallon",
        "quantity_is_int": False,
        "store_ids": []
    }).json()

    assert non_int_item["quantity_is_int"] is False