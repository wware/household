"""
Tests for Providers API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_provider(client: TestClient):
    """Test creating a new provider."""
    response = client.post("/api/providers", json={
        "name": "Dr. Smith",
        "phone": "555-0100",
        "email": "smith@example.com",
        "website": "https://drsmith.com",
        "address": "100 Main St\nCity, ST 12345",
        "info": "Board certified family medicine"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dr. Smith"
    assert data["phone"] == "555-0100"
    assert data["email"] == "smith@example.com"
    assert "id" in data


def test_create_minimal_provider(client: TestClient):
    """Test creating a provider with only required fields."""
    response = client.post("/api/providers", json={"name": "Dr. Minimal"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dr. Minimal"
    assert data["phone"] is None
    assert data["email"] is None


def test_list_providers(client: TestClient, sample_provider: dict):
    """Test listing all providers."""
    # Create another provider
    client.post("/api/providers", json={"name": "Dr. Another"})

    response = client.get("/api/providers")

    assert response.status_code == 200
    providers = response.json()
    assert len(providers) >= 2
    # Should be ordered by name
    names = [p["name"] for p in providers]
    assert names == sorted(names)


def test_get_provider(client: TestClient, sample_provider: dict):
    """Test getting a single provider by ID."""
    response = client.get(f"/api/providers/{sample_provider['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_provider["id"]
    assert data["name"] == sample_provider["name"]
    assert data["info"] == sample_provider["info"]


def test_get_nonexistent_provider(client: TestClient):
    """Test getting a provider that doesn't exist."""
    response = client.get("/api/providers/99999")

    assert response.status_code == 404


def test_update_provider_all_fields(client: TestClient, sample_provider: dict):
    """Test updating all fields of a provider."""
    response = client.put(
        f"/api/providers/{sample_provider['id']}",
        json={
            "name": "Dr. Updated",
            "phone": "555-9999",
            "email": "updated@example.com",
            "website": "https://updated.com",
            "address": "999 New St",
            "info": "Updated info"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dr. Updated"
    assert data["phone"] == "555-9999"
    assert data["email"] == "updated@example.com"


def test_update_provider_partial(client: TestClient, sample_provider: dict):
    """Test updating only some fields of a provider."""
    original_name = sample_provider["name"]

    response = client.put(
        f"/api/providers/{sample_provider['id']}",
        json={"phone": "555-NEWPHONE"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == original_name  # Unchanged
    assert data["phone"] == "555-NEWPHONE"  # Updated


def test_update_nonexistent_provider(client: TestClient):
    """Test updating a provider that doesn't exist."""
    response = client.put(
        "/api/providers/99999",
        json={"name": "New Name"}
    )

    assert response.status_code == 404


def test_delete_provider(client: TestClient, sample_provider: dict):
    """Test deleting a provider."""
    response = client.delete(f"/api/providers/{sample_provider['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/providers/{sample_provider['id']}")
    assert response.status_code == 404


def test_delete_provider_with_appointments(
    client: TestClient,
    sample_provider: dict,
    sample_user: dict
):
    """Test deleting a provider that has appointments fails."""
    # Create an appointment with this provider
    client.post("/api/appointments", json={
        "title": "Checkup",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "provider_id": sample_provider["id"],
        "patient_name": "Test Patient",
        "created_by": sample_user["id"]
    })

    response = client.delete(f"/api/providers/{sample_provider['id']}")

    assert response.status_code == 409
    assert "appointments reference this provider" in response.json()["detail"]


def test_delete_nonexistent_provider(client: TestClient):
    """Test deleting a provider that doesn't exist."""
    response = client.delete("/api/providers/99999")

    assert response.status_code == 404


def test_multiline_address(client: TestClient):
    """Test that multi-line addresses are stored correctly."""
    multiline_address = "123 Main Street\nSuite 456\nSpringfield, IL 62701\nUSA"

    response = client.post("/api/providers", json={
        "name": "Dr. Address Test",
        "address": multiline_address
    })

    assert response.status_code == 201
    data = response.json()
    assert data["address"] == multiline_address