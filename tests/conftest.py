"""
Pytest fixtures and configuration.

Provides shared test fixtures for database setup, test client, and sample data.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.database import DATABASE_PATH, SCHEMA_PATH, get_db


@pytest.fixture(scope="function")
def test_db() -> Generator[Path, None, None]:
    """
    Create a temporary test database for each test.

    Yields:
        Path to the temporary database file.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Initialize the database with schema
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

    # Temporarily override the DATABASE_PATH
    original_path = DATABASE_PATH
    import server.database
    server.database.DATABASE_PATH = Path(db_path)

    yield Path(db_path)

    # Cleanup
    server.database.DATABASE_PATH = original_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db: Path) -> TestClient:
    """
    Create a test client with a fresh database.

    Args:
        test_db: Test database fixture.

    Returns:
        FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_user(client: TestClient) -> dict:
    """
    Create a sample user for testing.

    Args:
        client: Test client fixture.

    Returns:
        Created user data.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email)
            VALUES ('Test User', 'test@example.com')
        """)
        user_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, name, email, created_at
            FROM users WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        return dict(row)


@pytest.fixture(scope="function")
def sample_store(client: TestClient) -> dict:
    """
    Create a sample store for testing.

    Args:
        client: Test client fixture.

    Returns:
        Created store data.
    """
    response = client.post("/api/stores", json={"name": "TestStore"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def sample_provider(client: TestClient) -> dict:
    """
    Create a sample provider for testing.

    Args:
        client: Test client fixture.

    Returns:
        Created provider data.
    """
    response = client.post("/api/providers", json={
        "name": "Dr. Test",
        "phone": "555-1234",
        "email": "dr.test@example.com",
        "website": "https://drtest.example.com",
        "address": "123 Test St\nTestville, TS 12345",
        "info": "General practitioner"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def sample_item(client: TestClient, sample_store: dict) -> dict:
    """
    Create a sample item for testing.

    Args:
        client: Test client fixture.
        sample_store: Sample store fixture.

    Returns:
        Created item data.
    """
    response = client.post("/api/items", json={
        "name": "Test Item",
        "default_quantity": "1",
        "quantity_is_int": True,
        "section": "Other",
        "store_ids": [sample_store["id"]]
    })
    assert response.status_code == 201
    return response.json()