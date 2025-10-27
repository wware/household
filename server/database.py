"""
Database connection and utilities.

Handles SQLite connection, initialization, and provides helper functions
for database operations.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


DATABASE_PATH = Path(__file__).parent.parent / "household.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a database connection.

    Returns:
        SQLite connection with row factory enabled for dict-like access.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Automatically commits on success and rolls back on error.

    Yields:
        Database connection.

    Example:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database by running the schema.sql file.

    This will create all tables, indexes, and constraints.
    Raises FileNotFoundError if schema.sql doesn't exist.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with get_db() as conn:
        cursor = conn.cursor()
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)

    print(f"Database initialized at {DATABASE_PATH}")


def reset_db() -> None:
    """
    Delete the database file and reinitialize from schema.

    WARNING: This will destroy all data!
    """
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"Deleted existing database: {DATABASE_PATH}")

    init_db()


if __name__ == "__main__":
    # Allow running this module directly to initialize the database
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_db()
    else:
        init_db()