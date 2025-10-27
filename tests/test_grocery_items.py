"""
Tests for Grocery Items API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_grocery_item(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test adding an item to grocery list."""
    response = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"],
        "quantity": "2"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == sample_item["id"]
    assert data["user_id"] == sample_user["id"]
    assert data["quantity"] == "2"
    assert data["purchased"] is False
    assert "item" in data
    assert data["item"]["name"] == sample_item["name"]


def test_create_grocery_item_with_int_quantity(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test creating grocery item with integer quantity."""
    response = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"],
        "quantity": "3",
        "int_quantity": 3
    })

    assert response.status_code == 201
    data = response.json()
    assert data["int_quantity"] == 3


def test_create_grocery_item_invalid_item(client: TestClient, sample_user: dict):
    """Test creating grocery item with invalid item_id fails."""
    response = client.post("/api/grocery-items", json={
        "item_id": 99999,
        "user_id": sample_user["id"]
    })

    assert response.status_code == 404
    assert "Item" in response.json()["detail"]


def test_create_grocery_item_invalid_user(
    client: TestClient,
    sample_item: dict
):
    """Test creating grocery item with invalid user_id fails."""
    response = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": 99999
    })

    assert response.status_code == 404
    assert "User" in response.json()["detail"]


def test_list_grocery_items(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test listing grocery items for a user."""
    # Create grocery items
    client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"]
    })

    response = client.get(f"/api/grocery-items?user_id={sample_user['id']}")

    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert all(i["user_id"] == sample_user["id"] for i in items)


def test_list_grocery_items_filter_by_store(
    client: TestClient,
    sample_user: dict
):
    """Test filtering grocery items by store."""
    # Create stores and items
    store1 = client.post("/api/stores", json={"name": "Store1"}).json()
    store2 = client.post("/api/stores", json={"name": "Store2"}).json()

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
        "store_ids": []
    }).json()

    # Add all to grocery list
    for item in [item1, item2, item3]:
        client.post("/api/grocery-items", json={
            "item_id": item["id"],
            "user_id": sample_user["id"]
        })

    # Filter by store1
    response = client.get(
        f"/api/grocery-items?user_id={sample_user['id']}&store_id={store1['id']}"
    )

    assert response.status_code == 200
    items = response.json()
    item_names = [i["item"]["name"] for i in items]
    assert "Item1" in item_names
    assert "Item3" in item_names  # Unspecified items
    assert "Item2" not in item_names


def test_get_grocery_item(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test getting a single grocery item."""
    created = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"]
    }).json()

    response = client.get(f"/api/grocery-items/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]


def test_update_grocery_item_quantity(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test updating grocery item quantity."""
    created = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"],
        "quantity": "1"
    }).json()

    response = client.put(
        f"/api/grocery-items/{created['id']}",
        json={"quantity": "5", "int_quantity": 5}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == "5"
    assert data["int_quantity"] == 5


def test_update_grocery_item_purchased(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test marking a grocery item as purchased."""
    created = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"]
    }).json()

    response = client.put(
        f"/api/grocery-items/{created['id']}",
        json={"purchased": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["purchased"] is True


def test_delete_grocery_item(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test removing an item from grocery list."""
    created = client.post("/api/grocery-items", json={
        "item_id": sample_item["id"],
        "user_id": sample_user["id"]
    }).json()

    response = client.delete(f"/api/grocery-items/{created['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/grocery-items/{created['id']}")
    assert response.status_code == 404


def test_grocery_items_ordered_by_created_at(
    client: TestClient,
    sample_user: dict
):
    """Test that grocery items are ordered by creation time (newest first)."""
    # Create multiple items
    item1 = client.post("/api/items", json={
        "name": "First",
        "store_ids": []
    }).json()

    item2 = client.post("/api/items", json={
        "name": "Second",
        "store_ids": []
    }).json()

    # Add to grocery list in order
    gi1 = client.post("/api/grocery-items", json={
        "item_id": item1["id"],
        "user_id": sample_user["id"]
    }).json()

    gi2 = client.post("/api/grocery-items", json={
        "item_id": item2["id"],
        "user_id": sample_user["id"]
    }).json()

    response = client.get(f"/api/grocery-items?user_id={sample_user['id']}")

    items = response.json()
    # Should have both items
    assert len(items) >= 2
    item_ids = [i["id"] for i in items]
    assert gi1["id"] in item_ids
    assert gi2["id"] in item_ids