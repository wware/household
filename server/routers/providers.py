"""
Providers API endpoints.

Manages healthcare providers, veterinarians, and other service providers.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from ..database import get_db
from ..models import Provider, ProviderCreate, ProviderUpdate


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=List[Provider])
def list_providers() -> List[Provider]:
    """
    List all providers.

    Returns:
        List of all providers ordered by name.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, email, website, address, info,
                   created_at, updated_at
            FROM providers
            ORDER BY name
        """)
        rows = cursor.fetchall()
        return [Provider(**dict(row)) for row in rows]


@router.post("", response_model=Provider, status_code=status.HTTP_201_CREATED)
def create_provider(provider: ProviderCreate) -> Provider:
    """
    Create a new provider.

    Args:
        provider: Provider data.

    Returns:
        The created provider.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO providers (name, phone, email, website, address, info)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (provider.name, provider.phone, provider.email,
              provider.website, provider.address, provider.info))

        provider_id = cursor.lastrowid

        cursor.execute("""
            SELECT id, name, phone, email, website, address, info,
                   created_at, updated_at
            FROM providers
            WHERE id = ?
        """, (provider_id,))

        row = cursor.fetchone()
        return Provider(**dict(row))


@router.get("/{provider_id}", response_model=Provider)
def get_provider(provider_id: int) -> Provider:
    """
    Get a provider by ID.

    Args:
        provider_id: Provider ID.

    Returns:
        The provider.

    Raises:
        HTTPException: 404 if provider not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, email, website, address, info,
                   created_at, updated_at
            FROM providers
            WHERE id = ?
        """, (provider_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with id {provider_id} not found"
            )

        return Provider(**dict(row))


@router.put("/{provider_id}", response_model=Provider)
def update_provider(
    provider_id: int,
    provider_update: ProviderUpdate
) -> Provider:
    """
    Update a provider.

    Args:
        provider_id: Provider ID.
        provider_update: Updated provider data.

    Returns:
        The updated provider.

    Raises:
        HTTPException: 404 if provider not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if provider exists
        cursor.execute("SELECT id FROM providers WHERE id = ?", (provider_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with id {provider_id} not found"
            )

        # Build update query dynamically
        update_fields = []
        update_values = []

        if provider_update.name is not None:
            update_fields.append("name = ?")
            update_values.append(provider_update.name)

        if provider_update.phone is not None:
            update_fields.append("phone = ?")
            update_values.append(provider_update.phone)

        if provider_update.email is not None:
            update_fields.append("email = ?")
            update_values.append(provider_update.email)

        if provider_update.website is not None:
            update_fields.append("website = ?")
            update_values.append(provider_update.website)

        if provider_update.address is not None:
            update_fields.append("address = ?")
            update_values.append(provider_update.address)

        if provider_update.info is not None:
            update_fields.append("info = ?")
            update_values.append(provider_update.info)

        # Update provider if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(provider_id)

            cursor.execute(f"""
                UPDATE providers
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Fetch and return updated provider
        cursor.execute("""
            SELECT id, name, phone, email, website, address, info,
                   created_at, updated_at
            FROM providers
            WHERE id = ?
        """, (provider_id,))

        row = cursor.fetchone()
        return Provider(**dict(row))


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: int) -> None:
    """
    Delete a provider.

    Args:
        provider_id: Provider ID.

    Raises:
        HTTPException: 404 if provider not found,
                      409 if provider has appointments.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if provider exists
        cursor.execute("SELECT id FROM providers WHERE id = ?", (provider_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with id {provider_id} not found"
            )

        # Check if provider has appointments
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM appointments
            WHERE provider_id = ?
        """, (provider_id,))

        count = cursor.fetchone()['count']
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot delete provider: "
                    f"{count} appointments reference this provider"
                )
            )

        cursor.execute("DELETE FROM providers WHERE id = ?", (provider_id,))