"""
Tests for Tasks API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_create_task(client: TestClient):
    """Test creating a task."""
    response = client.post("/api/tasks", json={
        "title": "Clean the garage",
        "category": "household",
        "due_date": "2025-11-30T00:00:00"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean the garage"
    assert data["category"] == "household"
    assert data["completed"] is False
    assert data["assigned_to"] is None


def test_create_task_with_assignment(
    client: TestClient,
    sample_user: dict
):
    """Test creating a task assigned to a user."""
    response = client.post("/api/tasks", json={
        "title": "Water plants",
        "category": "household",
        "assigned_to": sample_user["id"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["assigned_to"] == sample_user["id"]


def test_create_task_invalid_user(client: TestClient):
    """Test creating task with invalid user fails."""
    response = client.post("/api/tasks", json={
        "title": "Test Task",
        "category": "household",
        "assigned_to": 99999
    })

    assert response.status_code == 404


def test_list_tasks(client: TestClient):
    """Test listing all tasks."""
    client.post("/api/tasks", json={
        "title": "Task 1",
        "category": "household"
    })

    client.post("/api/tasks", json={
        "title": "Task 2",
        "category": "pet"
    })

    response = client.get("/api/tasks")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 2


def test_list_tasks_filter_by_assigned_to(
    client: TestClient,
    sample_user: dict
):
    """Test filtering tasks by assigned user."""
    # Create another user
    from server.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                      ("User2", "user2@example.com"))
        user2_id = cursor.lastrowid

    # Create tasks for different users
    client.post("/api/tasks", json={
        "title": "User 1 Task",
        "category": "household",
        "assigned_to": sample_user["id"]
    })

    client.post("/api/tasks", json={
        "title": "User 2 Task",
        "category": "household",
        "assigned_to": user2_id
    })

    response = client.get(f"/api/tasks?assigned_to={sample_user['id']}")

    assert response.status_code == 200
    tasks = response.json()
    assert all(t["assigned_to"] == sample_user["id"] for t in tasks)


def test_list_tasks_filter_by_category(client: TestClient):
    """Test filtering tasks by category."""
    client.post("/api/tasks", json={
        "title": "Household Task",
        "category": "household"
    })

    client.post("/api/tasks", json={
        "title": "Pet Task",
        "category": "pet"
    })

    response = client.get("/api/tasks?category=household")

    assert response.status_code == 200
    tasks = response.json()
    assert all(t["category"] == "household" for t in tasks)


def test_list_tasks_ordering(client: TestClient):
    """Test that tasks are ordered by completion status and due date."""
    # Create completed task
    completed = client.post("/api/tasks", json={
        "title": "Completed Task",
        "category": "household",
        "due_date": "2025-11-01T00:00:00"
    }).json()

    client.put(f"/api/tasks/{completed['id']}", json={"completed": True})

    # Create incomplete tasks with different due dates
    client.post("/api/tasks", json={
        "title": "Due Soon",
        "category": "household",
        "due_date": "2025-11-15T00:00:00"
    })

    client.post("/api/tasks", json={
        "title": "Due Later",
        "category": "household",
        "due_date": "2025-12-01T00:00:00"
    })

    client.post("/api/tasks", json={
        "title": "No Due Date",
        "category": "household"
    })

    response = client.get("/api/tasks")

    tasks = response.json()
    # Incomplete tasks should come first
    incomplete_tasks = [t for t in tasks if not t["completed"]]
    assert len(incomplete_tasks) >= 3

    # Among incomplete tasks, those with due dates come first
    has_due_date = [t for t in incomplete_tasks if t["due_date"] is not None]
    assert has_due_date[0]["title"] == "Due Soon"


def test_get_task(client: TestClient):
    """Test getting a single task."""
    created = client.post("/api/tasks", json={
        "title": "Test Task",
        "category": "household"
    }).json()

    response = client.get(f"/api/tasks/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["title"] == "Test Task"


def test_update_task_complete(client: TestClient):
    """Test marking a task as completed."""
    created = client.post("/api/tasks", json={
        "title": "Task to Complete",
        "category": "household"
    }).json()

    response = client.put(
        f"/api/tasks/{created['id']}",
        json={"completed": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True


def test_update_task_reassign(client: TestClient, sample_user: dict):
    """Test reassigning a task."""
    created = client.post("/api/tasks", json={
        "title": "Task to Reassign",
        "category": "household"
    }).json()

    response = client.put(
        f"/api/tasks/{created['id']}",
        json={"assigned_to": sample_user["id"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to"] == sample_user["id"]


def test_update_task_partial(client: TestClient):
    """Test partially updating a task."""
    created = client.post("/api/tasks", json={
        "title": "Original Title",
        "category": "household",
        "due_date": "2025-11-01T00:00:00"
    }).json()

    # Update only the title
    response = client.put(
        f"/api/tasks/{created['id']}",
        json={"title": "Updated Title"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["category"] == "household"  # Unchanged
    assert data["due_date"] is not None  # Unchanged


def test_delete_task(client: TestClient):
    """Test deleting a task."""
    created = client.post("/api/tasks", json={
        "title": "Task to Delete",
        "category": "household"
    }).json()

    response = client.delete(f"/api/tasks/{created['id']}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/tasks/{created['id']}")
    assert response.status_code == 404


def test_task_categories(client: TestClient):
    """Test different task categories."""
    categories = ["household", "pet", "maintenance", "travel", "other"]

    for category in categories:
        response = client.post("/api/tasks", json={
            "title": f"{category} task",
            "category": category
        })

        assert response.status_code == 201
        assert response.json()["category"] == category


def test_task_without_due_date(client: TestClient):
    """Test creating a task without a due date."""
    response = client.post("/api/tasks", json={
        "title": "No Rush",
        "category": "household"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["due_date"] is None


def test_multiple_tasks_same_user(client: TestClient, sample_user: dict):
    """Test creating multiple tasks for the same user."""
    for i in range(3):
        response = client.post("/api/tasks", json={
            "title": f"Task {i+1}",
            "category": "household",
            "assigned_to": sample_user["id"]
        })

        assert response.status_code == 201

    response = client.get(f"/api/tasks?assigned_to={sample_user['id']}")

    tasks = response.json()
    assert len(tasks) == 3