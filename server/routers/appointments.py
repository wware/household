"""
Appointments API endpoints.

Manages medical, pet, and other appointments.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..database import get_db
from ..models import (
    Appointment, AppointmentCreate, AppointmentUpdate,
    AppointmentWithProvider, Provider
)


router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def _get_provider(cursor, provider_id: int) -> Optional[Provider]:
    """Helper function to get provider details."""
    if provider_id is None:
        return None

    cursor.execute("""
        SELECT id, name, phone, email, website, address, info,
               created_at, updated_at
        FROM providers
        WHERE id = ?
    """, (provider_id,))

    row = cursor.fetchone()
    if row:
        return Provider(**dict(row))
    return None


@router.get("", response_model=List[AppointmentWithProvider])
def list_appointments(
    created_by: Optional[int] = Query(
        None, description="Filter by user who created"
    ),
    patient_name: Optional[str] = Query(
        None, description="Filter by patient name"
    )
) -> List[AppointmentWithProvider]:
    """
    List appointments with optional filtering.

    Args:
        created_by: Optional user ID to filter by creator.
        patient_name: Optional patient name to filter by.

    Returns:
        List of appointments with provider details, ordered by date.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, title, date, type, notes, provider_id,
                   patient_name, created_by, created_at, updated_at
            FROM appointments
            WHERE 1=1
        """
        params = []

        if created_by is not None:
            query += " AND created_by = ?"
            params.append(created_by)

        if patient_name is not None:
            query += " AND patient_name = ?"
            params.append(patient_name)

        query += " ORDER BY date"

        cursor.execute(query, tuple(params))

        appointments = []
        for row in cursor.fetchall():
            appt_data = dict(row)
            provider = _get_provider(cursor, appt_data.get('provider_id'))
            appointments.append(
                AppointmentWithProvider(**appt_data, provider=provider)
            )

        return appointments


@router.post(
    "",
    response_model=AppointmentWithProvider,
    status_code=status.HTTP_201_CREATED
)
def create_appointment(
    appointment: AppointmentCreate
) -> AppointmentWithProvider:
    """
    Create a new appointment.

    Args:
        appointment: Appointment data.

    Returns:
        The created appointment with provider details.

    Raises:
        HTTPException: 404 if user or provider not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate created_by user exists
        cursor.execute(
            "SELECT id FROM users WHERE id = ?",
            (appointment.created_by,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {appointment.created_by} not found"
            )

        # Validate provider exists if provided
        if appointment.provider_id is not None:
            cursor.execute(
                "SELECT id FROM providers WHERE id = ?",
                (appointment.provider_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Provider with id {appointment.provider_id} "
                        f"not found"
                    )
                )

        # Insert appointment
        cursor.execute("""
            INSERT INTO appointments (
                title, date, type, notes, provider_id,
                patient_name, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment.title, appointment.date, appointment.type,
            appointment.notes, appointment.provider_id,
            appointment.patient_name, appointment.created_by
        ))

        appt_id = cursor.lastrowid

        # Fetch and return created appointment
        cursor.execute("""
            SELECT id, title, date, type, notes, provider_id,
                   patient_name, created_by, created_at, updated_at
            FROM appointments
            WHERE id = ?
        """, (appt_id,))

        row = cursor.fetchone()
        appt_data = dict(row)
        provider = _get_provider(cursor, appt_data.get('provider_id'))

        return AppointmentWithProvider(**appt_data, provider=provider)


@router.get("/{appointment_id}", response_model=AppointmentWithProvider)
def get_appointment(appointment_id: int) -> AppointmentWithProvider:
    """
    Get an appointment by ID.

    Args:
        appointment_id: Appointment ID.

    Returns:
        The appointment with provider details.

    Raises:
        HTTPException: 404 if appointment not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, date, type, notes, provider_id,
                   patient_name, created_by, created_at, updated_at
            FROM appointments
            WHERE id = ?
        """, (appointment_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with id {appointment_id} not found"
            )

        appt_data = dict(row)
        provider = _get_provider(cursor, appt_data.get('provider_id'))

        return AppointmentWithProvider(**appt_data, provider=provider)


@router.put("/{appointment_id}", response_model=AppointmentWithProvider)
def update_appointment(
    appointment_id: int,
    update: AppointmentUpdate
) -> AppointmentWithProvider:
    """
    Update an appointment.

    Args:
        appointment_id: Appointment ID.
        update: Updated appointment data.

    Returns:
        The updated appointment with provider details.

    Raises:
        HTTPException: 404 if appointment or provider not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if appointment exists
        cursor.execute(
            "SELECT id FROM appointments WHERE id = ?",
            (appointment_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with id {appointment_id} not found"
            )

        # Validate provider exists if being updated
        if update.provider_id is not None:
            cursor.execute(
                "SELECT id FROM providers WHERE id = ?",
                (update.provider_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Provider with id {update.provider_id} not found"
                    )
                )

        # Build update query dynamically
        update_fields = []
        update_values = []

        if update.title is not None:
            update_fields.append("title = ?")
            update_values.append(update.title)

        if update.date is not None:
            update_fields.append("date = ?")
            update_values.append(update.date)

        if update.type is not None:
            update_fields.append("type = ?")
            update_values.append(update.type)

        if update.notes is not None:
            update_fields.append("notes = ?")
            update_values.append(update.notes)

        if update.provider_id is not None:
            update_fields.append("provider_id = ?")
            update_values.append(update.provider_id)

        if update.patient_name is not None:
            update_fields.append("patient_name = ?")
            update_values.append(update.patient_name)

        # Update appointment if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(appointment_id)

            cursor.execute(f"""
                UPDATE appointments
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Fetch and return updated appointment
        cursor.execute("""
            SELECT id, title, date, type, notes, provider_id,
                   patient_name, created_by, created_at, updated_at
            FROM appointments
            WHERE id = ?
        """, (appointment_id,))

        row = cursor.fetchone()
        appt_data = dict(row)
        provider = _get_provider(cursor, appt_data.get('provider_id'))

        return AppointmentWithProvider(**appt_data, provider=provider)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int) -> None:
    """
    Delete an appointment.

    Args:
        appointment_id: Appointment ID.

    Raises:
        HTTPException: 404 if appointment not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if appointment exists
        cursor.execute(
            "SELECT id FROM appointments WHERE id = ?",
            (appointment_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with id {appointment_id} not found"
            )

        cursor.execute(
            "DELETE FROM appointments WHERE id = ?",
            (appointment_id,)
        )