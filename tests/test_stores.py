"""
Tests for Stores API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_store(client: TestClient):
    """Test creating a new store."""
    response = client.post("/api/stores", json={"name": "Whole Foods"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Whole Foods"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_duplicate_store(client: TestClient, sample_store: dict):
    """Test creating a store with duplicate name fails."""
    response = client.post("/api/stores", json={"name": sample_store["name"]})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_list_stores(client: TestClient, sample_store: dict):
    """Test listing all stores."""
    # Create another store
    client.post("/api/stores", json={"name": "Trader Joes"})

    response = client.get("/api/stores")

    assert response.status_code == 200
    stores = response.json()
    assert len(stores) >= 2
    assert any(s["name"] == sample_store["name"] for s in stores)


def test_get_store(client: TestClient, sample_store: dict):
    """Test getting a single store by ID."""
    response = client.get(f"/api/stores/{sample_store['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_store["id"]
    assert data["name"] == sample_store["name"]


def test_get_nonexistent_store(client: TestClient):
    """Test getting a store that doesn't exist."""
    response = client.get("/api/stores/99999")

    assert response.status_code == 404


def test_update_store(client: TestClient, sample_store: dict):
    """Test updating a store."""
    response = client.put(
        f"/api/stores/{sample_store['id']}",
        json={"name": "Updated Store"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Store"
    assert data["id"] == sample_store["id"]


def test_update_store_duplicate_name(client: TestClient, sample_store: dict):
    """Test updating a store to a duplicate name fails."""
    # Create another store
    other = client.post("/api/stores", json={"name": "Other Store"}).json()

    # Try to rename sample_store to Other Store
    response = client.put(
        f"/api/stores/{sample_store['id']}",
        json={"name": "Other Store"}
    )

    assert response.status_code == 409


def test_update_nonexistent_store(client: TestClient):
    """Test updating a store that doesn't exist."""
    response = client.put("/api/stores/99999", json={"name": "New Name"})

    assert response.status_code == 404


def test_delete_store(client: TestClient, sample_store: dict):
    """Test deleting a store."""
    response = client.delete(f"/api/stores/{sample_store['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/stores/{sample_store['id']}")
    assert response.status_code == 404


def test_delete_store_with_items(
    client: TestClient,
    sample_store: dict,
    sample_item: dict
):
    """Test deleting a store that has items fails."""
    response = client.delete(f"/api/stores/{sample_store['id']}")

    assert response.status_code == 409
    assert "items reference this store" in response.json()["detail"]


def test_delete_nonexistent_store(client: TestClient):
    """Test deleting a store that doesn't exist."""
    response = client.delete("/api/stores/99999")

    assert response.status_code == 404