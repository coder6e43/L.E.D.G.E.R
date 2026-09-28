"""
database/connection.py

Owns the SQLite connection for the LEDGER project.
Other modules (auth, calculation, query) should import get_connection()
from here rather than opening their own sqlite3 connections.
"""

import sqlite3
import os
from contextlib import contextmanager

# Single source of truth for where the DB file lives.
# Override with the LEDGER_DB_PATH env var if needed (e.g. for tests).
DB_PATH = os.environ.get("LEDGER_DB_PATH", os.path.join("data", "ledger.db"))


def get_raw_connection() -> sqlite3.Connection:
    """
    Returns a new sqlite3 connection with sensible defaults:
    - row_factory set so rows behave like dicts (row["column"])
    - foreign keys enforced (SQLite has them off by default)
    """
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_connection():
    """
    Preferred way to use the DB elsewhere:

        from database.connection import get_connection
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM expenses").fetchall()

    Commits on success, rolls back on exception, always closes.
    """
    conn = get_raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def db_exists() -> bool:
    return os.path.exists(DB_PATH)