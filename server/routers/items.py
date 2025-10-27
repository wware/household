"""
Items API endpoints.

Manages item definitions (groceries, pet supplies, household items, etc.).
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from ..database import get_db
from ..models import Item, ItemCreate, ItemUpdate, ItemWithStores, Store


router = APIRouter(prefix="/api/items", tags=["items"])


def _get_item_stores(cursor, item_id: int) -> List[Store]:
    """Helper function to get stores for an item."""
    cursor.execute("""
        SELECT s.id, s.name, s.created_at, s.updated_at
        FROM stores s
        JOIN item_stores ist ON s.id = ist.store_id
        WHERE ist.item_id = ?
        ORDER BY s.name
    """, (item_id,))

    return [Store(**dict(row)) for row in cursor.fetchall()]


def _set_item_stores(cursor, item_id: int, store_ids: List[int]) -> None:
    """Helper function to set stores for an item."""
    # Delete existing associations
    cursor.execute("DELETE FROM item_stores WHERE item_id = ?", (item_id,))

    # Insert new associations
    for store_id in store_ids:
        cursor.execute("""
            INSERT INTO item_stores (item_id, store_id)
            VALUES (?, ?)
        """, (item_id, store_id))


@router.get("", response_model=List[ItemWithStores])
def list_items(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    section: Optional[str] = Query(None, description="Filter by section")
) -> List[ItemWithStores]:
    """
    List all items with optional filtering.

    Args:
        store_id: Optional store ID to filter by.
        section: Optional section to filter by.

    Returns:
        List of items with their associated stores.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query based on filters
        if store_id is not None:
            # Items available at this store OR items with no specific store
            cursor.execute("""
                SELECT DISTINCT i.id, i.name, i.default_quantity, i.quantity_is_int,
                       i.section, i.created_at, i.updated_at
                FROM items i
                LEFT JOIN item_stores ist ON i.id = ist.item_id
                WHERE (ist.store_id = ? OR ist.store_id IS NULL)
                  AND (? IS NULL OR i.section = ?)
                ORDER BY i.name
            """, (store_id, section, section))
        else:
            cursor.execute("""
                SELECT id, name, default_quantity, quantity_is_int,
                       section, created_at, updated_at
                FROM items
                WHERE ? IS NULL OR section = ?
                ORDER BY name
            """, (section, section))

        items = []
        for row in cursor.fetchall():
            item_data = dict(row)
            item_id = item_data['id']
            stores = _get_item_stores(cursor, item_id)
            items.append(ItemWithStores(**item_data, stores=stores))

        return items


@router.post("", response_model=ItemWithStores, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate) -> ItemWithStores:
    """
    Create a new item.

    Args:
        item: Item data including store associations.

    Returns:
        The created item with stores.

    Raises:
        HTTPException: 409 if an item with this name already exists,
                      404 if any store_id doesn't exist.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check for duplicate name
        cursor.execute("SELECT id FROM items WHERE name = ?", (item.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item with name '{item.name}' already exists"
            )

        # Validate store IDs
        for store_id in item.store_ids:
            cursor.execute("SELECT id FROM stores WHERE id = ?", (store_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Store with id {store_id} not found"
                )

        # Insert item
        cursor.execute("""
            INSERT INTO items (name, default_quantity, quantity_is_int, section)
            VALUES (?, ?, ?, ?)
        """, (item.name, item.default_quantity, item.quantity_is_int, item.section))

        item_id = cursor.lastrowid

        # Set store associations
        _set_item_stores(cursor, item_id, item.store_ids)

        # Fetch and return created item with stores
        cursor.execute("""
            SELECT id, name, default_quantity, quantity_is_int,
                   section, created_at, updated_at
            FROM items
            WHERE id = ?
        """, (item_id,))

        row = cursor.fetchone()
        item_data = dict(row)
        stores = _get_item_stores(cursor, item_id)

        return ItemWithStores(**item_data, stores=stores)


@router.get("/{item_id}", response_model=ItemWithStores)
def get_item(item_id: int) -> ItemWithStores:
    """
    Get an item by ID.

    Args:
        item_id: Item ID.

    Returns:
        The item with associated stores.

    Raises:
        HTTPException: 404 if item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, default_quantity, quantity_is_int,
                   section, created_at, updated_at
            FROM items
            WHERE id = ?
        """, (item_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )

        item_data = dict(row)
        stores = _get_item_stores(cursor, item_id)

        return ItemWithStores(**item_data, stores=stores)


@router.put("/{item_id}", response_model=ItemWithStores)
def update_item(item_id: int, item_update: ItemUpdate) -> ItemWithStores:
    """
    Update an item.

    Args:
        item_id: Item ID.
        item_update: Updated item data.

    Returns:
        The updated item with stores.

    Raises:
        HTTPException: 404 if item not found, 409 if name conflicts.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if item exists
        cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )

        # Build update query dynamically
        update_fields = []
        update_values = []

        if item_update.name is not None:
            # Check for duplicate name
            cursor.execute(
                "SELECT id FROM items WHERE name = ? AND id != ?",
                (item_update.name, item_id)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Item with name '{item_update.name}' already exists"
                )
            update_fields.append("name = ?")
            update_values.append(item_update.name)

        if item_update.default_quantity is not None:
            update_fields.append("default_quantity = ?")
            update_values.append(item_update.default_quantity)

        if item_update.quantity_is_int is not None:
            update_fields.append("quantity_is_int = ?")
            update_values.append(item_update.quantity_is_int)

        if item_update.section is not None:
            update_fields.append("section = ?")
            update_values.append(item_update.section)

        # Update item if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(item_id)

            cursor.execute(f"""
                UPDATE items
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Update store associations if provided
        if item_update.store_ids is not None:
            # Validate store IDs
            for store_id in item_update.store_ids:
                cursor.execute("SELECT id FROM stores WHERE id = ?", (store_id,))
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Store with id {store_id} not found"
                    )

            _set_item_stores(cursor, item_id, item_update.store_ids)

        # Fetch and return updated item with stores
        cursor.execute("""
            SELECT id, name, default_quantity, quantity_is_int,
                   section, created_at, updated_at
            FROM items
            WHERE id = ?
        """, (item_id,))

        row = cursor.fetchone()
        item_data = dict(row)
        stores = _get_item_stores(cursor, item_id)

        return ItemWithStores(**item_data, stores=stores)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    """
    Delete an item.

    Args:
        item_id: Item ID.

    Raises:
        HTTPException: 404 if item not found.

    Note:
        This will cascade delete all grocery items and template items
        that reference this item due to ON DELETE CASCADE constraints.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if item exists
        cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )

        # Delete will cascade to item_stores, grocery_items, and grocery_template_items
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))