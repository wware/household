"""
Tests for Grocery Templates API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_template(client: TestClient, sample_user: dict):
    """Test creating a grocery template."""
    response = client.post("/api/grocery-templates", json={
        "name": "Weekly Groceries",
        "is_default": False,
        "user_id": sample_user["id"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Weekly Groceries"
    assert data["user_id"] == sample_user["id"]
    assert data["is_default"] is False


def test_create_default_template(client: TestClient, sample_user: dict):
    """Test creating a default template unsets other defaults."""
    # Create first default template
    template1 = client.post("/api/grocery-templates", json={
        "name": "Template 1",
        "is_default": True,
        "user_id": sample_user["id"]
    }).json()

    assert template1["is_default"] is True

    # Create second default template
    template2 = client.post("/api/grocery-templates", json={
        "name": "Template 2",
        "is_default": True,
        "user_id": sample_user["id"]
    }).json()

    assert template2["is_default"] is True

    # Check that template1 is no longer default
    response = client.get(f"/api/grocery-templates/{template1['id']}")
    assert response.json()["is_default"] is False


def test_list_templates(client: TestClient, sample_user: dict):
    """Test listing templates for a user."""
    client.post("/api/grocery-templates", json={
        "name": "Template A",
        "user_id": sample_user["id"]
    })

    client.post("/api/grocery-templates", json={
        "name": "Template B",
        "is_default": True,
        "user_id": sample_user["id"]
    })

    response = client.get(f"/api/grocery-templates?user_id={sample_user['id']}")

    assert response.status_code == 200
    templates = response.json()
    assert len(templates) == 2
    # Default should be first
    assert templates[0]["is_default"] is True


def test_get_template_with_items(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test getting a template with its items."""
    # Create template
    template = client.post("/api/grocery-templates", json={
        "name": "Test Template",
        "user_id": sample_user["id"]
    }).json()

    # Add item to template
    client.post(f"/api/grocery-templates/{template['id']}/items", json={
        "item_id": sample_item["id"],
        "quantity": "2",
        "template_id": template["id"]
    })

    response = client.get(f"/api/grocery-templates/{template['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template["id"]
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["item"]["name"] == sample_item["name"]


def test_update_template_name(client: TestClient, sample_user: dict):
    """Test updating a template's name."""
    template = client.post("/api/grocery-templates", json={
        "name": "Original Name",
        "user_id": sample_user["id"]
    }).json()

    response = client.put(
        f"/api/grocery-templates/{template['id']}",
        json={"name": "New Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


def test_update_template_to_default(client: TestClient, sample_user: dict):
    """Test updating a template to be the default."""
    template1 = client.post("/api/grocery-templates", json={
        "name": "Template 1",
        "is_default": True,
        "user_id": sample_user["id"]
    }).json()

    template2 = client.post("/api/grocery-templates", json={
        "name": "Template 2",
        "is_default": False,
        "user_id": sample_user["id"]
    }).json()

    # Make template2 the default
    response = client.put(
        f"/api/grocery-templates/{template2['id']}",
        json={"is_default": True}
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True

    # Check template1 is no longer default
    response = client.get(f"/api/grocery-templates/{template1['id']}")
    assert response.json()["is_default"] is False


def test_delete_template(client: TestClient, sample_user: dict):
    """Test deleting a template."""
    template = client.post("/api/grocery-templates", json={
        "name": "To Delete",
        "user_id": sample_user["id"]
    }).json()

    response = client.delete(f"/api/grocery-templates/{template['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/grocery-templates/{template['id']}")
    assert response.status_code == 404


def test_add_item_to_template(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test adding an item to a template."""
    template = client.post("/api/grocery-templates", json={
        "name": "Test Template",
        "user_id": sample_user["id"]
    }).json()

    response = client.post(
        f"/api/grocery-templates/{template['id']}/items",
        json={
            "item_id": sample_item["id"],
            "quantity": "3",
            "template_id": template["id"]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == sample_item["id"]
    assert data["quantity"] == "3"
    assert data["item"]["name"] == sample_item["name"]


def test_add_item_to_nonexistent_template(
    client: TestClient,
    sample_item: dict
):
    """Test adding item to nonexistent template fails."""
    response = client.post(
        "/api/grocery-templates/99999/items",
        json={
            "item_id": sample_item["id"],
            "template_id": 99999
        }
    )

    assert response.status_code == 404


def test_remove_item_from_template(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test removing an item from a template."""
    template = client.post("/api/grocery-templates", json={
        "name": "Test Template",
        "user_id": sample_user["id"]
    }).json()

    template_item = client.post(
        f"/api/grocery-templates/{template['id']}/items",
        json={
            "item_id": sample_item["id"],
            "template_id": template["id"]
        }
    ).json()

    response = client.delete(
        f"/api/grocery-templates/{template['id']}/items/{template_item['id']}"
    )

    assert response.status_code == 204


def test_apply_template(
    client: TestClient,
    sample_user: dict,
    sample_item: dict
):
    """Test applying a template to create grocery items."""
    # Create template with items
    template = client.post("/api/grocery-templates", json={
        "name": "Test Template",
        "user_id": sample_user["id"]
    }).json()

    client.post(f"/api/grocery-templates/{template['id']}/items", json={
        "item_id": sample_item["id"],
        "quantity": "2",
        "template_id": template["id"]
    })

    # Apply template
    response = client.post(
        f"/api/grocery-templates/{template['id']}/apply",
        params={"user_id": sample_user["id"]}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["items_added"] == 1
    assert data["template_id"] == template["id"]

    # Verify grocery items were created
    grocery_items = client.get(
        f"/api/grocery-items?user_id={sample_user['id']}"
    ).json()

    assert len(grocery_items) == 1
    assert grocery_items[0]["item_id"] == sample_item["id"]


def test_apply_template_uses_default_quantity(
    client: TestClient,
    sample_user: dict
):
    """Test that applying template uses default quantity when not overridden."""
    # Create item with default quantity
    item = client.post("/api/items", json={
        "name": "Test Item",
        "default_quantity": "1 lb",
        "quantity_is_int": False,
        "store_ids": []
    }).json()

    # Create template without quantity override
    template = client.post("/api/grocery-templates", json={
        "name": "Test Template",
        "user_id": sample_user["id"]
    }).json()

    client.post(f"/api/grocery-templates/{template['id']}/items", json={
        "item_id": item["id"],
        "template_id": template["id"]
        # No quantity specified
    })

    # Apply template
    client.post(
        f"/api/grocery-templates/{template['id']}/apply",
        params={"user_id": sample_user["id"]}
    )

    # Check grocery item has default quantity
    grocery_items = client.get(
        f"/api/grocery-items?user_id={sample_user['id']}"
    ).json()

    assert grocery_items[0]["quantity"] == "1 lb"


def test_apply_empty_template(client: TestClient, sample_user: dict):
    """Test applying an empty template creates no items."""
    template = client.post("/api/grocery-templates", json={
        "name": "Empty Template",
        "user_id": sample_user["id"]
    }).json()

    response = client.post(
        f"/api/grocery-templates/{template['id']}/apply",
        params={"user_id": sample_user["id"]}
    )

    assert response.status_code == 201
    assert response.json()["items_added"] == 0