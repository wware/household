"""
Tasks API endpoints.

Manages household tasks with categories and assignment.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from ..database import get_db
from ..models import Task, TaskCreate, TaskUpdate


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[Task])
def list_tasks(
    assigned_to: Optional[int] = Query(None, description="Filter by assigned user ID"),
    category: Optional[str] = Query(None, description="Filter by category")
) -> List[Task]:
    """
    List tasks with optional filtering.

    Args:
        assigned_to: Optional user ID to filter by assignment.
        category: Optional category to filter by.

    Returns:
        List of tasks ordered by due date.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query based on filters
        query = """
            SELECT id, title, category, completed, due_date, assigned_to,
                   created_at, updated_at
            FROM tasks
            WHERE 1=1
        """
        params = []

        if assigned_to is not None:
            query += " AND assigned_to = ?"
            params.append(assigned_to)

        if category is not None:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY completed, due_date NULLS LAST, created_at DESC"

        cursor.execute(query, tuple(params))
        return [Task(**dict(row)) for row in cursor.fetchall()]


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> Task:
    """
    Create a new task.

    Args:
        task: Task data.

    Returns:
        The created task.

    Raises:
        HTTPException: 404 if assigned_to user not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Validate assigned_to user exists if provided
        if task.assigned_to is not None:
            cursor.execute("SELECT id FROM users WHERE id = ?", (task.assigned_to,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {task.assigned_to} not found"
                )

        # Insert task
        cursor.execute("""
            INSERT INTO tasks (title, category, due_date, assigned_to)
            VALUES (?, ?, ?, ?)
        """, (task.title, task.category, task.due_date, task.assigned_to))

        task_id = cursor.lastrowid

        # Fetch and return created task
        cursor.execute("""
            SELECT id, title, category, completed, due_date, assigned_to,
                   created_at, updated_at
            FROM tasks
            WHERE id = ?
        """, (task_id,))

        row = cursor.fetchone()
        return Task(**dict(row))


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    """
    Get a task by ID.

    Args:
        task_id: Task ID.

    Returns:
        The task.

    Raises:
        HTTPException: 404 if task not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, category, completed, due_date, assigned_to,
                   created_at, updated_at
            FROM tasks
            WHERE id = ?
        """, (task_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )

        return Task(**dict(row))


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: int, update: TaskUpdate) -> Task:
    """
    Update a task.

    Args:
        task_id: Task ID.
        update: Updated task data.

    Returns:
        The updated task.

    Raises:
        HTTPException: 404 if task or assigned_to user not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if task exists
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )

        # Build update query dynamically
        update_fields = []
        update_values = []

        if update.title is not None:
            update_fields.append("title = ?")
            update_values.append(update.title)

        if update.category is not None:
            update_fields.append("category = ?")
            update_values.append(update.category)

        if update.completed is not None:
            update_fields.append("completed = ?")
            update_values.append(update.completed)

        if update.due_date is not None:
            update_fields.append("due_date = ?")
            update_values.append(update.due_date)

        if update.assigned_to is not None:
            # Validate assigned_to user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (update.assigned_to,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {update.assigned_to} not found"
                )

            update_fields.append("assigned_to = ?")
            update_values.append(update.assigned_to)

        # Update task if there are fields to update
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(task_id)

            cursor.execute(f"""
                UPDATE tasks
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, tuple(update_values))

        # Fetch and return updated task
        cursor.execute("""
            SELECT id, title, category, completed, due_date, assigned_to,
                   created_at, updated_at
            FROM tasks
            WHERE id = ?
        """, (task_id,))

        row = cursor.fetchone()
        return Task(**dict(row))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    """
    Delete a task.

    Args:
        task_id: Task ID.

    Raises:
        HTTPException: 404 if task not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if task exists
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))