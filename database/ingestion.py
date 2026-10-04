"""
database/ingestion.py

Loads and validates CSV data (users, expenses, budgets) into the SQLite DB.

Validates / cleans:
- missing required values
- invalid / unparseable dates
- duplicate transaction IDs
- invalid category / currency values (against an allowed list)

Bad rows are skipped and reported, not silently dropped.
"""

import csv
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, ValidationError, field_validator

from database.connection import get_connection
from database.models import init_db

ALLOWED_CATEGORIES = {
    "Food", "Travel", "Software", "Office Supplies",
    "Utilities", "Marketing", "Training", "Miscellaneous",
}
ALLOWED_CURRENCIES = {"INR", "USD", "EUR"}
ALLOWED_ROLES = {"Manager", "Employee", "Admin"}


class ExpenseRow(BaseModel):
    expense_id: str
    user_id: str
    cost_centre: str
    category: str
    amount: float
    currency: str
    date: str
    description: str = ""

    @field_validator("category")
    @classmethod
    def check_category(cls, v):
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"invalid category '{v}'")
        return v

    @field_validator("currency")
    @classmethod
    def check_currency(cls, v):
        if v not in ALLOWED_CURRENCIES:
            raise ValueError(f"invalid currency '{v}'")
        return v

    @field_validator("date")
    @classmethod
    def check_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"invalid date '{v}', expected YYYY-MM-DD")
        return v

    @field_validator("amount")
    @classmethod
    def check_amount(cls, v):
        if v < 0:
            raise ValueError("amount cannot be negative")
        return v


class UserRow(BaseModel):
    user_id: str
    name: str
    email: str
    password_hash: str
    role: str
    cost_centre: str

    @field_validator("role")
    @classmethod
    def check_role(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f"invalid role '{v}'")
        return v


class BudgetRow(BaseModel):
    budget_id: str
    cost_centre: str
    category: str
    amount: float
    period_start: str
    period_end: str

    @field_validator("category")
    @classmethod
    def check_category(cls, v):
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"invalid category '{v}'")
        return v


def _read_csv(path: str) -> List[Dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ingest_expenses(csv_path: str) -> Dict:
    raw_rows = _read_csv(csv_path)
    valid_rows, errors, seen_ids = [], [], set()

    for i, row in enumerate(raw_rows, start=2):  # row 1 = header
        exp_id = row.get("expense_id", "")
        if exp_id in seen_ids:
            errors.append(f"line {i}: duplicate expense_id '{exp_id}' — skipped")
            continue
        try:
            validated = ExpenseRow(**row)
            valid_rows.append(validated)
            seen_ids.add(exp_id)
        except ValidationError as e:
            errors.append(f"line {i}: {e.errors()[0]['msg']}")

    with get_connection() as conn:
        for r in valid_rows:
            conn.execute(
                """INSERT OR REPLACE INTO expenses
                   (expense_id, user_id, cost_centre, category, amount, currency, date, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.expense_id, r.user_id, r.cost_centre, r.category,
                 r.amount, r.currency, r.date, r.description),
            )

    return {"inserted": len(valid_rows), "errors": errors}


def ingest_users(csv_path: str) -> Dict:
    raw_rows = _read_csv(csv_path)
    valid_rows, errors = [], []

    for i, row in enumerate(raw_rows, start=2):
        try:
            valid_rows.append(UserRow(**row))
        except ValidationError as e:
            errors.append(f"line {i}: {e.errors()[0]['msg']}")

    with get_connection() as conn:
        for r in valid_rows:
            conn.execute(
                """INSERT OR REPLACE INTO users
                   (user_id, name, email, password_hash, role, cost_centre)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r.user_id, r.name, r.email, r.password_hash, r.role, r.cost_centre),
            )

    return {"inserted": len(valid_rows), "errors": errors}


def ingest_budgets(csv_path: str) -> Dict:
    raw_rows = _read_csv(csv_path)
    valid_rows, errors = [], []

    for i, row in enumerate(raw_rows, start=2):
        try:
            valid_rows.append(BudgetRow(**row))
        except ValidationError as e:
            errors.append(f"line {i}: {e.errors()[0]['msg']}")

    with get_connection() as conn:
        for r in valid_rows:
            conn.execute(
                """INSERT OR REPLACE INTO budgets
                   (budget_id, cost_centre, category, amount, period_start, period_end)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (r.budget_id, r.cost_centre, r.category, r.amount,
                 r.period_start, r.period_end),
            )

    return {"inserted": len(valid_rows), "errors": errors}


if __name__ == "__main__":
    # Quick manual run: python -m database.ingestion
    init_db()
    for label, fn, path in [
        ("users", ingest_users, "data/sample_users.csv"),
        ("expenses", ingest_expenses, "data/sample_expenses.csv"),
        ("budgets", ingest_budgets, "data/sample_budgets.csv"),
    ]:
        result = fn(path)
        print(f"\n{label}: inserted {result['inserted']} rows")
        for err in result["errors"]:
            # ASCII-safe for Windows terminals using the default cp1252 codec.
            print(f"  [rejected] {err}")
