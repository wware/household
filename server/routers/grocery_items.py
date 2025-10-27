"""
Grocery Items API endpoints.

Manages items on users' active grocery lists.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from ..database import get_db
from ..models import (
    GroceryItem, GroceryItemCreate, GroceryItemUpdate,
    GroceryItemWithDetails, ItemWithStores, Store
)


router = APIRouter(prefix="/api/grocery-items", tags=["grocery-items"])


def _get_item_with_stores(cursor, item_id: int) -> ItemWithStores:
    """Helper function to get item details with stores."""
    cursor.execute("""
        SELECT id, name, default_quantity, quantity_is_int,
               section, created_at, updated_at
        FROM items
        WHERE id = ?
    """, (item_id,))

    item_row = cursor.fetchone()
    if not item_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )

    item_data = dict(item_row)

    # Get stores for this item
    cursor.execute("""
        SELECT s.id, s.name, s.created_at, s.updated_at
        FROM stores s
        JOIN item_stores ist ON s.id = ist.store_id
        WHERE ist.item_id = ?
        ORDER BY s.name
    """, (item_id,))

    stores = [Store(**dict(row)) for row in cursor.fetchall()]

    return ItemWithStores(**item_data, stores=stores)


@router.get("", response_model=List[GroceryItemWithDetails])
def list_grocery_items(
    user_id: int = Query(..., description="User ID to filter by"),
    store_id: Optional[int] = Query(None, description="Filter by store ID")
) -> List[GroceryItemWithDetails]:
    """
    List grocery items for a user.

    Args:
        user_id: User ID (required).
        store_id: Optional store ID to filter by items available at that store.

    Returns:
        List of grocery items with full item details and stores.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        if store_id is not None:
            # Get items available at this store OR items with no specific store
            cursor.execute("""
                SELECT DISTINCT gi.id, gi.item_id, gi.quantity, gi.int_quantity,
                       gi.purchased, gi.user_id, gi.created_at, gi.updated_at
                FROM grocery_items gi
                JOIN items i ON gi.item_id = i.id
                LEFT JOIN item_stores ist ON i.id = ist.item_id
                WHERE gi.user_id = ?
                  AND (ist.store_id = ? OR ist.store_id IS NULL)
                ORDER BY gi.created_at DESC
            """, (user_id, store_id))
        else:
            cursor.execute("""
                SELECT id, item_id, quantity, int_quantity, purchased,
                       user_id, created_at, updated_at
                FROM grocery_items
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))

        grocery_items = []
        for row in cursor.fetchall():
            gi_data = dict(row)
            item = _get_item_with_stores(cursor, gi_data['item_id'])
            grocery_items.append(GroceryItemWithDetails(**gi_data, item=item))

        return grocery_items


@router.post("", response_model=GroceryItemWithDetails, status_code=status.HTTP_201_CREATED)
def create_grocery_item(grocery_item: GroceryItemCreate) -> GroceryItemWithDetails:
    """
    Add an item to the grocery list.

    Args:
        grocery_item: Grocery item data.

    Returns:
        The created grocery item with full item details.

    Raises:
        HTTPException: 404 if item or user not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate item exists
        cursor.execute("SELECT id FROM items WHERE id = ?", (grocery_item.item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {grocery_item.item_id} not found"
            )

        # Validate user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (grocery_item.user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {grocery_item.user_id} not found"
            )

        # Insert grocery item
        cursor.execute("""
            INSERT INTO grocery_items (item_id, quantity, int_quantity, user_id)
            VALUES (?, ?, ?, ?)
        """, (grocery_item.item_id, grocery_item.quantity,
              grocery_item.int_quantity, grocery_item.user_id))

        gi_id = cursor.lastrowid

        # Fetch and return created grocery item with details
        cursor.execute("""
            SELECT id, item_id, quantity, int_quantity, purchased,
                   user_id, created_at, updated_at
            FROM grocery_items
            WHERE id = ?
        """, (gi_id,))

        row = cursor.fetchone()
        gi_data = dict(row)
        item = _get_item_with_stores(cursor, gi_data['item_id'])

        return GroceryItemWithDetails(**gi_data, item=item)


@router.get("/{grocery_item_id}", response_model=GroceryItemWithDetails)
def get_grocery_item(grocery_item_id: int) -> GroceryItemWithDetails:
    """
    Get a grocery item by ID.

    Args:
        grocery_item_id: Grocery item ID.

    Returns:
        The grocery item with full item details.

    Raises:
        HTTPException: 404 if grocery item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, item_id, quantity, int_quantity, purchased,
                   user_id, created_at, updated_at
            FROM grocery_items
            WHERE id = ?
        """, (grocery_item_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grocery item with id {grocery_item_id} not found"
            )

        gi_data = dict(row)
        item = _get_item_with_stores(cursor, gi_data['item_id'])

        return GroceryItemWithDetails(**gi_data, item=item)


@router.put("/{grocery_item_id}", response_model=GroceryItemWithDetails)
def update_grocery_item(
    grocery_item_id: int,
    update: GroceryItemUpdate
) -> GroceryItemWithDetails:
    """
    Update a grocery item.

    Args:
        grocery_item_id: Grocery item ID.
        update: Updated grocery item data.

    Returns:
        The updated grocery item with full item details.

    Raises:
        HTTPException: 404 if grocery item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if grocery item exists
        cursor.execute("SELECT id FROM grocery_items WHERE id = ?", (grocery_item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grocery item with id {grocery_item_id} not found"
            )

        # Build update query dynamically
        update_fields = []
        update_values = []

        if update.quantity is not None:
            update_fields.append("quantity = ?")
            update_values.append(update.quantity)

        if update.int_quantity is not None:
            update_fields.append("int_quantity = ?")
            update_values.append(update.int_quantity)

        if update.purchased is not None:
            update_fields.append("purchased = ?")
            update_values.append(update.purchased)

        # Update grocery item if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(grocery_item_id)

            cursor.execute(f"""
                UPDATE grocery_items
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Fetch and return updated grocery item with details
        cursor.execute("""
            SELECT id, item_id, quantity, int_quantity, purchased,
                   user_id, created_at, updated_at
            FROM grocery_items
            WHERE id = ?
        """, (grocery_item_id,))

        row = cursor.fetchone()
        gi_data = dict(row)
        item = _get_item_with_stores(cursor, gi_data['item_id'])

        return GroceryItemWithDetails(**gi_data, item=item)


@router.delete("/{grocery_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grocery_item(grocery_item_id: int) -> None:
    """
    Remove an item from the grocery list.

    Args:
        grocery_item_id: Grocery item ID.

    Raises:
        HTTPException: 404 if grocery item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if grocery item exists
        cursor.execute("SELECT id FROM grocery_items WHERE id = ?", (grocery_item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grocery item with id {grocery_item_id} not found"
            )

        cursor.execute("DELETE FROM grocery_items WHERE id = ?", (grocery_item_id,))