"""
database/models.py

Defines the LEDGER schema: users, expenses, budgets.
Run `python -m database.models` (or call init_db()) to create the tables.

Schema notes for the team:
- user_id / cost_centre are the two fields RBAC (Shubham) will check.
- expenses.category is what the query compiler (Niketan) maps synonyms onto.
- expenses + budgets are what the calculation engine (Shaurya) reads.
  He should only ever read via database/connection.py, filtered by the
  authorized cost_centre that auth/rbac.py hands him.
"""

from database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('Manager', 'Employee', 'Admin')),
    cost_centre   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    expense_id  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    cost_centre TEXT NOT NULL,
    category    TEXT NOT NULL,
    amount      REAL NOT NULL CHECK (amount >= 0),
    currency    TEXT NOT NULL DEFAULT 'INR',
    date        TEXT NOT NULL,              -- ISO format: YYYY-MM-DD
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS budgets (
    budget_id     TEXT PRIMARY KEY,
    cost_centre   TEXT NOT NULL,
    category      TEXT NOT NULL,
    amount        REAL NOT NULL CHECK (amount >= 0),
    period_start  TEXT NOT NULL,            -- ISO format: YYYY-MM-DD
    period_end    TEXT NOT NULL             -- ISO format: YYYY-MM-DD
);

-- Speeds up the filters the calculation engine will run constantly.
CREATE INDEX IF NOT EXISTS idx_expenses_cost_centre ON expenses (cost_centre);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date);
CREATE INDEX IF NOT EXISTS idx_budgets_cost_centre ON budgets (cost_centre);
"""


def init_db():
    """Creates all tables (safe to re-run; uses IF NOT EXISTS)."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
    print("LEDGER database schema created/verified.")


if __name__ == "__main__":
    init_db()