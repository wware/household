"""
Stores API endpoints.

Manages store entities for tracking where items can be purchased.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from ..database import get_db
from ..models import Store, StoreCreate, StoreUpdate


router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("", response_model=List[Store])
def list_stores() -> List[Store]:
    """
    List all stores.

    Returns:
        List of all stores in the system.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at, updated_at
            FROM stores
            ORDER BY name
        """)
        rows = cursor.fetchall()
        return [Store(**dict(row)) for row in rows]


@router.post("", response_model=Store, status_code=status.HTTP_201_CREATED)
def create_store(store: StoreCreate) -> Store:
    """
    Create a new store.

    Args:
        store: Store data.

    Returns:
        The created store.

    Raises:
        HTTPException: 409 if a store with this name already exists.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check for duplicate name
        cursor.execute("SELECT id FROM stores WHERE name = ?", (store.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Store with name '{store.name}' already exists"
            )

        cursor.execute("""
            INSERT INTO stores (name)
            VALUES (?)
        """, (store.name,))

        store_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, name, created_at, updated_at
            FROM stores
            WHERE id = ?
        """, (store_id,))

        row = cursor.fetchone()
        return Store(**dict(row))


@router.get("/{store_id}", response_model=Store)
def get_store(store_id: int) -> Store:
    """
    Get a store by ID.

    Args:
        store_id: Store ID.

    Returns:
        The store.

    Raises:
        HTTPException: 404 if store not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at, updated_at
            FROM stores
            WHERE id = ?
        """, (store_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {store_id} not found"
            )

        return Store(**dict(row))


@router.put("/{store_id}", response_model=Store)
def update_store(store_id: int, store_update: StoreUpdate) -> Store:
    """
    Update a store.

    Args:
        store_id: Store ID.
        store_update: Updated store data.

    Returns:
        The updated store.

    Raises:
        HTTPException: 404 if store not found, 409 if name conflicts.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if store exists
        cursor.execute("SELECT id FROM stores WHERE id = ?", (store_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {store_id} not found"
            )

        # Update only provided fields
        if store_update.name is not None:
            # Check for duplicate name
            cursor.execute(
                "SELECT id FROM stores WHERE name = ? AND id != ?",
                (store_update.name, store_id)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Store with name '{store_update.name}' already exists"
                )

            cursor.execute("""
                UPDATE stores
                SET name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (store_update.name, store_id))

        # Fetch and return updated store
        cursor.execute("""
            SELECT id, name, created_at, updated_at
            FROM stores
            WHERE id = ?
        """, (store_id,))

        row = cursor.fetchone()
        return Store(**dict(row))


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(store_id: int) -> None:
    """
    Delete a store.

    Args:
        store_id: Store ID.

    Raises:
        HTTPException: 404 if store not found, 409 if store is in use.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if store exists
        cursor.execute("SELECT id FROM stores WHERE id = ?", (store_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {store_id} not found"
            )

        # Check if store is referenced by any items
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM item_stores
            WHERE store_id = ?
        """, (store_id,))

        count = cursor.fetchone()['count']
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete store: {count} items reference this store"
            )

        cursor.execute("DELETE FROM stores WHERE id = ?", (store_id,))