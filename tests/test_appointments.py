"""
Tests for Appointments API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_appointment_with_provider(
    client: TestClient,
    sample_user: dict,
    sample_provider: dict
):
    """Test creating an appointment with a provider."""
    response = client.post("/api/appointments", json={
        "title": "Annual Checkup",
        "date": "2025-11-15T14:00:00",
        "type": "medical",
        "notes": "Bring insurance card",
        "provider_id": sample_provider["id"],
        "patient_name": "John Doe",
        "created_by": sample_user["id"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Annual Checkup"
    assert data["provider_id"] == sample_provider["id"]
    assert data["patient_name"] == "John Doe"
    assert "provider" in data
    assert data["provider"]["name"] == sample_provider["name"]


def test_create_appointment_without_provider(
    client: TestClient,
    sample_user: dict
):
    """Test creating an appointment without a provider."""
    response = client.post("/api/appointments", json={
        "title": "Dentist",
        "date": "2025-12-01T09:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["provider_id"] is None
    assert data["provider"] is None


def test_create_appointment_invalid_provider(client: TestClient, sample_user: dict):
    """Test creating appointment with invalid provider fails."""
    response = client.post("/api/appointments", json={
        "title": "Test",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "provider_id": 99999,
        "created_by": sample_user["id"]
    })

    assert response.status_code == 404
    assert "Provider" in response.json()["detail"]


def test_create_appointment_invalid_user(client: TestClient):
    """Test creating appointment with invalid user fails."""
    response = client.post("/api/appointments", json={
        "title": "Test",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": 99999
    })

    assert response.status_code == 404
    assert "User" in response.json()["detail"]


def test_list_appointments(
    client: TestClient,
    sample_user: dict,
    sample_provider: dict
):
    """Test listing all appointments."""
    client.post("/api/appointments", json={
        "title": "Appointment 1",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    })

    client.post("/api/appointments", json={
        "title": "Appointment 2",
        "date": "2025-11-02T11:00:00",
        "type": "pet",
        "provider_id": sample_provider["id"],
        "created_by": sample_user["id"]
    })

    response = client.get("/api/appointments")

    assert response.status_code == 200
    appointments = response.json()
    assert len(appointments) >= 2


def test_list_appointments_filter_by_creator(
    client: TestClient,
    sample_user: dict
):
    """Test filtering appointments by creator."""
    # Create another user
    from server.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                      ("User2", "user2@example.com"))
        user2_id = cursor.lastrowid

    # Create appointments for different users
    client.post("/api/appointments", json={
        "title": "User 1 Appointment",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    })

    client.post("/api/appointments", json={
        "title": "User 2 Appointment",
        "date": "2025-11-02T10:00:00",
        "type": "medical",
        "created_by": user2_id
    })

    response = client.get(f"/api/appointments?created_by={sample_user['id']}")

    assert response.status_code == 200
    appointments = response.json()
    assert all(a["created_by"] == sample_user["id"] for a in appointments)


def test_list_appointments_filter_by_patient(
    client: TestClient,
    sample_user: dict
):
    """Test filtering appointments by patient name."""
    client.post("/api/appointments", json={
        "title": "Patient A Appointment",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "patient_name": "Patient A",
        "created_by": sample_user["id"]
    })

    client.post("/api/appointments", json={
        "title": "Patient B Appointment",
        "date": "2025-11-02T10:00:00",
        "type": "medical",
        "patient_name": "Patient B",
        "created_by": sample_user["id"]
    })

    response = client.get("/api/appointments?patient_name=Patient A")

    assert response.status_code == 200
    appointments = response.json()
    assert all(a["patient_name"] == "Patient A" for a in appointments)


def test_list_appointments_ordered_by_date(
    client: TestClient,
    sample_user: dict
):
    """Test that appointments are ordered by date."""
    # Create appointments out of order
    client.post("/api/appointments", json={
        "title": "Later",
        "date": "2025-12-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    })

    client.post("/api/appointments", json={
        "title": "Earlier",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    })

    response = client.get("/api/appointments")

    appointments = response.json()
    # Should be ordered by date
    assert appointments[0]["title"] == "Earlier"
    assert appointments[1]["title"] == "Later"


def test_get_appointment(
    client: TestClient,
    sample_user: dict,
    sample_provider: dict
):
    """Test getting a single appointment."""
    created = client.post("/api/appointments", json={
        "title": "Test Appointment",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "provider_id": sample_provider["id"],
        "created_by": sample_user["id"]
    }).json()

    response = client.get(f"/api/appointments/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["provider"]["id"] == sample_provider["id"]


def test_update_appointment(
    client: TestClient,
    sample_user: dict
):
    """Test updating an appointment."""
    created = client.post("/api/appointments", json={
        "title": "Original Title",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    }).json()

    response = client.put(
        f"/api/appointments/{created['id']}",
        json={
            "title": "Updated Title",
            "notes": "Added notes"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["notes"] == "Added notes"


def test_update_appointment_change_provider(
    client: TestClient,
    sample_user: dict,
    sample_provider: dict
):
    """Test changing an appointment's provider."""
    created = client.post("/api/appointments", json={
        "title": "Test",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    }).json()

    response = client.put(
        f"/api/appointments/{created['id']}",
        json={"provider_id": sample_provider["id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == sample_provider["id"]
    assert data["provider"]["name"] == sample_provider["name"]


def test_delete_appointment(
    client: TestClient,
    sample_user: dict
):
    """Test deleting an appointment."""
    created = client.post("/api/appointments", json={
        "title": "To Delete",
        "date": "2025-11-01T10:00:00",
        "type": "medical",
        "created_by": sample_user["id"]
    }).json()

    response = client.delete(f"/api/appointments/{created['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/appointments/{created['id']}")
    assert response.status_code == 404


def test_appointment_types(client: TestClient, sample_user: dict):
    """Test different appointment types."""
    for appt_type in ["medical", "pet", "other"]:
        response = client.post("/api/appointments", json={
            "title": f"{appt_type} appointment",
            "date": "2025-11-01T10:00:00",
            "type": appt_type,
            "created_by": sample_user["id"]
        })

        assert response.status_code == 201
        assert response.json()["type"] == appt_type


def test_pet_appointment_scenario(
    client: TestClient,
    sample_user: dict,
    sample_provider: dict
):
    """Test a realistic pet appointment scenario."""
    response = client.post("/api/appointments", json={
        "title": "Annual Vet Checkup",
        "date": "2025-11-15T14:00:00",
        "type": "pet",
        "notes": "Vaccination due",
        "provider_id": sample_provider["id"],
        "patient_name": "Fluffy (cat)",
        "created_by": sample_user["id"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "pet"
    assert "Fluffy" in data["patient_name"]