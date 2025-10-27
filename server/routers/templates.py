"""
Grocery Templates API endpoints.

Manages templates for bulk-adding items to grocery lists.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List

from ..database import get_db
from ..models import (
    GroceryTemplate, GroceryTemplateCreate, GroceryTemplateUpdate,
    GroceryTemplateWithItems, GroceryTemplateItem, GroceryTemplateItemCreate,
    GroceryTemplateItemWithDetails, ItemWithStores, Store
)


router = APIRouter(prefix="/api/grocery-templates", tags=["templates"])


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


@router.get("", response_model=List[GroceryTemplate])
def list_templates(
    user_id: int = Query(..., description="User ID to filter by")
) -> List[GroceryTemplate]:
    """
    List grocery templates for a user.

    Args:
        user_id: User ID (required).

    Returns:
        List of templates (without items).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, is_default, user_id, created_at, updated_at
            FROM grocery_templates
            WHERE user_id = ?
            ORDER BY is_default DESC, name
        """, (user_id,))

        return [GroceryTemplate(**dict(row)) for row in cursor.fetchall()]


@router.post("", response_model=GroceryTemplate, status_code=status.HTTP_201_CREATED)
def create_template(template: GroceryTemplateCreate) -> GroceryTemplate:
    """
    Create a new grocery template.

    Args:
        template: Template data.

    Returns:
        The created template.

    Raises:
        HTTPException: 404 if user not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (template.user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {template.user_id} not found"
            )

        # If this is being set as default, unset other defaults for this user
        if template.is_default:
            cursor.execute("""
                UPDATE grocery_templates
                SET is_default = 0
                WHERE user_id = ?
            """, (template.user_id,))

        # Insert template
        cursor.execute("""
            INSERT INTO grocery_templates (name, is_default, user_id)
            VALUES (?, ?, ?)
        """, (template.name, template.is_default, template.user_id))

        template_id = cursor.lastrowid

        # Fetch and return created template
        cursor.execute("""
            SELECT id, name, is_default, user_id, created_at, updated_at
            FROM grocery_templates
            WHERE id = ?
        """, (template_id,))

        row = cursor.fetchone()
        return GroceryTemplate(**dict(row))


@router.get("/{template_id}", response_model=GroceryTemplateWithItems)
def get_template(template_id: int) -> GroceryTemplateWithItems:
    """
    Get a template by ID with all its items.

    Args:
        template_id: Template ID.

    Returns:
        The template with all its items and item details.

    Raises:
        HTTPException: 404 if template not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get template
        cursor.execute("""
            SELECT id, name, is_default, user_id, created_at, updated_at
            FROM grocery_templates
            WHERE id = ?
        """, (template_id,))

        template_row = cursor.fetchone()
        if not template_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {template_id} not found"
            )

        template_data = dict(template_row)

        # Get template items
        cursor.execute("""
            SELECT id, item_id, quantity, template_id, created_at
            FROM grocery_template_items
            WHERE template_id = ?
            ORDER BY created_at
        """, (template_id,))

        items = []
        for row in cursor.fetchall():
            ti_data = dict(row)
            item = _get_item_with_stores(cursor, ti_data['item_id'])
            items.append(GroceryTemplateItemWithDetails(**ti_data, item=item))

        return GroceryTemplateWithItems(**template_data, items=items)


@router.put("/{template_id}", response_model=GroceryTemplate)
def update_template(
    template_id: int,
    update: GroceryTemplateUpdate
) -> GroceryTemplate:
    """
    Update a template's metadata.

    Args:
        template_id: Template ID.
        update: Updated template data.

    Returns:
        The updated template.

    Raises:
        HTTPException: 404 if template not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if template exists and get user_id
        cursor.execute("SELECT user_id FROM grocery_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {template_id} not found"
            )

        user_id = row['user_id']

        # Build update query dynamically
        update_fields = []
        update_values = []

        if update.name is not None:
            update_fields.append("name = ?")
            update_values.append(update.name)

        if update.is_default is not None:
            # If setting as default, unset other defaults for this user
            if update.is_default:
                cursor.execute("""
                    UPDATE grocery_templates
                    SET is_default = 0
                    WHERE user_id = ? AND id != ?
                """, (user_id, template_id))

            update_fields.append("is_default = ?")
            update_values.append(update.is_default)

        # Update template if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(template_id)

            cursor.execute(f"""
                UPDATE grocery_templates
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Fetch and return updated template
        cursor.execute("""
            SELECT id, name, is_default, user_id, created_at, updated_at
            FROM grocery_templates
            WHERE id = ?
        """, (template_id,))

        row = cursor.fetchone()
        return GroceryTemplate(**dict(row))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int) -> None:
    """
    Delete a template.

    Args:
        template_id: Template ID.

    Raises:
        HTTPException: 404 if template not found.

    Note:
        This will cascade delete all template items due to ON DELETE CASCADE.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if template exists
        cursor.execute("SELECT id FROM grocery_templates WHERE id = ?", (template_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {template_id} not found"
            )

        cursor.execute("DELETE FROM grocery_templates WHERE id = ?", (template_id,))


@router.post("/{template_id}/items", response_model=GroceryTemplateItemWithDetails, status_code=status.HTTP_201_CREATED)
def add_item_to_template(
    template_id: int,
    template_item: GroceryTemplateItemCreate
) -> GroceryTemplateItemWithDetails:
    """
    Add an item to a template.

    Args:
        template_id: Template ID.
        template_item: Template item data.

    Returns:
        The created template item with full item details.

    Raises:
        HTTPException: 404 if template or item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate template exists
        cursor.execute("SELECT id FROM grocery_templates WHERE id = ?", (template_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {template_id} not found"
            )

        # Validate item exists
        cursor.execute("SELECT id FROM items WHERE id = ?", (template_item.item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {template_item.item_id} not found"
            )

        # Insert template item
        cursor.execute("""
            INSERT INTO grocery_template_items (item_id, quantity, template_id)
            VALUES (?, ?, ?)
        """, (template_item.item_id, template_item.quantity, template_id))

        ti_id = cursor.lastrowid

        # Fetch and return created template item with details
        cursor.execute("""
            SELECT id, item_id, quantity, template_id, created_at
            FROM grocery_template_items
            WHERE id = ?
        """, (ti_id,))

        row = cursor.fetchone()
        ti_data = dict(row)
        item = _get_item_with_stores(cursor, ti_data['item_id'])

        return GroceryTemplateItemWithDetails(**ti_data, item=item)


@router.delete("/{template_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_template(template_id: int, item_id: int) -> None:
    """
    Remove an item from a template.

    Args:
        template_id: Template ID.
        item_id: Template item ID (the ID from grocery_template_items table).

    Raises:
        HTTPException: 404 if template item not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if template item exists
        cursor.execute("""
            SELECT id FROM grocery_template_items
            WHERE id = ? AND template_id = ?
        """, (item_id, template_id))

        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template item with id {item_id} not found in template {template_id}"
            )

        cursor.execute("DELETE FROM grocery_template_items WHERE id = ?", (item_id,))


@router.post("/{template_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_template(template_id: int, user_id: int = Query(..., description="User to apply template for")) -> dict:
    """
    Apply a template to a user's grocery list.

    This creates grocery items for all items in the template.

    Args:
        template_id: Template ID.
        user_id: User ID to create grocery items for.

    Returns:
        Summary of items added.

    Raises:
        HTTPException: 404 if template or user not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate template exists
        cursor.execute("SELECT id FROM grocery_templates WHERE id = ?", (template_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {template_id} not found"
            )

        # Validate user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        # Get all template items
        cursor.execute("""
            SELECT item_id, quantity
            FROM grocery_template_items
            WHERE template_id = ?
        """, (template_id,))

        template_items = cursor.fetchall()
        items_added = 0

        # Create grocery items for each template item
        for ti_row in template_items:
            item_id = ti_row['item_id']
            quantity = ti_row['quantity']

            # Parse int_quantity if item has quantity_is_int set
            cursor.execute("""
                SELECT quantity_is_int, default_quantity
                FROM items
                WHERE id = ?
            """, (item_id,))

            item_row = cursor.fetchone()
            quantity_is_int = item_row['quantity_is_int']
            default_quantity = item_row['default_quantity']

            # Use template quantity or item default
            final_quantity = quantity or default_quantity
            int_quantity = None

            if quantity_is_int and final_quantity:
                try:
                    int_quantity = int(final_quantity)
                except ValueError:
                    pass

            cursor.execute("""
                INSERT INTO grocery_items (item_id, quantity, int_quantity, user_id, purchased)
                VALUES (?, ?, ?, ?, 0)
            """, (item_id, final_quantity, int_quantity, user_id))

            items_added += 1

        return {
            "template_id": template_id,
            "user_id": user_id,
            "items_added": items_added
        }