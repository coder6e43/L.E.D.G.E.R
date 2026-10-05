import datetime
import os

import pytest

from database.models import init_db
from database.connection import get_connection


@pytest.fixture()
def db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_ledger.db"

    monkeypatch.setenv("LEDGER_DB_PATH", str(db_path))

    import database.connection as connection_module
    monkeypatch.setattr(connection_module, "DB_PATH", str(db_path))

    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users
            (user_id, name, email, password_hash, role, cost_centre)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("U001", "User One", "u1@test.com", "hash", "Employee", "CC-TECH"),
        )

        conn.execute(
            """
            INSERT INTO users
            (user_id, name, email, password_hash, role, cost_centre)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("U002", "User Two", "u2@test.com", "hash", "Employee", "CC-TECH"),
        )

        conn.execute(
            """
            INSERT INTO users
            (user_id, name, email, password_hash, role, cost_centre)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("U003", "Manager", "manager@test.com", "hash", "Manager", "CC-SALES"),
        )

        expenses = [
            (
                "EXP-001",
                "U001",
                "CC-TECH",
                "Food",
                1000,
                "INR",
                "2026-09-01",
                "Lunch",
            ),
            (
                "EXP-002",
                "U001",
                "CC-TECH",
                "Food",
                2000,
                "INR",
                "2026-09-15",
                "Dinner",
            ),
            (
                "EXP-003",
                "U002",
                "CC-TECH",
                "Travel",
                1200,
                "INR",
                "2026-09-05",
                "Cab",
            ),
            (
                "EXP-004",
                "U002",
                "CC-TECH",
                "Travel",
                50,
                "USD",
                "2026-09-12",
                "Taxi",
            ),
            (
                "EXP-005",
                "U003",
                "CC-SALES",
                "Food",
                9999,
                "INR",
                "2026-09-05",
                "Client dinner",
            ),
        ]

        conn.executemany(
            """
            INSERT INTO expenses
            (expense_id, user_id, cost_centre, category, amount,
             currency, date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            expenses,
        )

        conn.execute(
            """
            INSERT INTO budgets
            (budget_id, cost_centre, category, amount, period_start, period_end)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "BUD-001",
                "CC-TECH",
                "Food",
                5000,
                "2026-09-01",
                "2026-09-30",
            ),
        )

        conn.commit()

    import calculation.engine as engine

    import importlib
    importlib.reload(engine)

    return db_path


# ---------------------------------------------------------------------------
# Trusted authorization scopes
# ---------------------------------------------------------------------------

@pytest.fixture()
def employee_u001_scope():
    return {
        "user_id": "U001",
        "role": "Employee",
        "scope_type": "user",
        "scope_user_id": "U001",
    }


@pytest.fixture()
def employee_u002_scope():
    return {
        "user_id": "U002",
        "role": "Employee",
        "scope_type": "user",
        "scope_user_id": "U002",
    }


@pytest.fixture()
def manager_scope():
    return {
        "user_id": "U003",
        "role": "Manager",
        "scope_type": "cost_centre",
        "cost_centre": "CC-SALES",
    }


@pytest.fixture()
def admin_scope():
    return {
        "user_id": "ADMIN",
        "role": "Admin",
        "scope_type": "organization",
    }


# ---------------------------------------------------------------------------
# Basic calculations
# ---------------------------------------------------------------------------

def test_sum_expenses_employee(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "category": "Food",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 3000
    assert result["currency"] == "INR"
    assert result["source_rows"] == ["EXP-001", "EXP-002"]


def test_category_breakdown(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "category_breakdown",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == {"Food": 3000}


def test_count_expenses(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "count_expenses",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 2
    assert set(result["source_rows"]) == {"EXP-001", "EXP-002"}


def test_top_transactions(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "top_transactions",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
            "limit": 1,
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert len(result["result"]) == 1
    assert result["result"][0]["expense_id"] == "EXP-002"
    assert result["result"][0]["amount"] == 2000


# ---------------------------------------------------------------------------
# Employee isolation
# ---------------------------------------------------------------------------

def test_employee_scope_isolates_user_data(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 3000
    assert "EXP-003" not in result["source_rows"]
    assert "EXP-005" not in result["source_rows"]


def test_employee_cannot_override_user_scope(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "user_scope": "U002",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "USER_SCOPE_CONFLICT"
    assert result["result"] is None
    assert result["source_rows"] == []


def test_employee_matching_user_scope_is_allowed(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "user_scope": "U001",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 3000


def test_employee_scope_cannot_be_missing_user_id(db):
    from calculation.engine import run_calculation

    scope = {
        "user_id": "U001",
        "role": "Employee",
        "scope_type": "user",
    }

    result = run_calculation(
        {"intent": "sum_expenses"},
        scope,
    )

    assert result["status"] == "MISSING_SCOPE_USER_ID"


# ---------------------------------------------------------------------------
# Manager / cost-centre isolation
# ---------------------------------------------------------------------------

def test_manager_scope_uses_authorized_cost_centre(db, manager_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "currency": "INR",
        },
        manager_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 9999
    assert result["source_rows"] == ["EXP-005"]


def test_manager_cannot_override_cost_centre(db, manager_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "user_scope": "CC-TECH",
            "currency": "INR",
        },
        manager_scope,
    )

    assert result["status"] == "USER_SCOPE_CONFLICT"


def test_manager_missing_cost_centre_fails_closed(db):
    from calculation.engine import run_calculation

    scope = {
        "user_id": "U003",
        "role": "Manager",
        "scope_type": "cost_centre",
    }

    result = run_calculation(
        {"intent": "sum_expenses"},
        scope,
    )

    assert result["status"] == "MISSING_COST_CENTRE"


# ---------------------------------------------------------------------------
# Organization / Admin scope
# ---------------------------------------------------------------------------

def test_admin_can_access_organization_data(db, admin_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "currency": "INR",
        },
        admin_scope,
    )

    assert result["status"] == "SUCCESS"

    # U001 Food = 3000
    # U002 Travel = 1200
    # U003 Food = 9999
    assert result["result"] == 14199

    assert "EXP-001" in result["source_rows"]
    assert "EXP-002" in result["source_rows"]
    assert "EXP-005" in result["source_rows"]


def test_admin_query_scope_is_rejected(db, admin_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "user_scope": "CC-TECH",
            "currency": "INR",
        },
        admin_scope,
    )

    assert result["status"] == "USER_SCOPE_CONFLICT"


# ---------------------------------------------------------------------------
# Invalid / missing authorization scope
# ---------------------------------------------------------------------------

def test_missing_authorized_scope(db):
    from calculation.engine import run_calculation

    result = run_calculation(
        {"intent": "sum_expenses"},
        None,
    )

    assert result["status"] == "MISSING_AUTHORIZED_SCOPE"


def test_invalid_scope_type(db):
    from calculation.engine import run_calculation

    result = run_calculation(
        {"intent": "sum_expenses"},
        {
            "scope_type": "ALL",
        },
    )

    assert result["status"] == "INVALID_SCOPE_TYPE"


def test_empty_scope_fails_closed(db):
    from calculation.engine import run_calculation

    result = run_calculation(
        {"intent": "sum_expenses"},
        {},
    )

    assert result["status"] == "MISSING_AUTHORIZED_SCOPE"


# ---------------------------------------------------------------------------
# Currency safety
# ---------------------------------------------------------------------------

def test_mixed_currency_is_rejected(db, employee_u002_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
        },
        employee_u002_scope,
    )

    assert result["status"] == "MIXED_CURRENCY"
    assert result["result"] is None
    assert result["source_rows"] == []


def test_explicit_currency_filters_before_calculation(db, employee_u002_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "currency": "INR",
        },
        employee_u002_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 1200
    assert result["currency"] == "INR"
    assert result["source_rows"] == ["EXP-003"]


def test_count_does_not_require_currency_consistency(db, employee_u002_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "count_expenses",
        },
        employee_u002_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 2


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

def test_date_range_filters_expenses(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "date_range_start": "2026-09-15",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 2000
    assert result["source_rows"] == ["EXP-002"]


def test_invalid_date_format_is_rejected(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "date_range_start": "2026-9-1",
        },
        employee_u001_scope,
    )

    assert result["status"] == "INVALID_DATE"


def test_impossible_date_is_rejected(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "sum_expenses",
            "date_range_start": "2026-02-30",
        },
        employee_u001_scope,
    )

    assert result["status"] == "INVALID_DATE"


# ---------------------------------------------------------------------------
# Budget calculations
# ---------------------------------------------------------------------------

def test_remaining_budget_manager(db, admin_scope, manager_scope):
    from calculation.engine import run_calculation

    # Manager's CC-SALES has no budget in our seed data.
    result = run_calculation(
        {
            "intent": "remaining_budget",
            "category": "Food",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        manager_scope,
    )

    assert result["status"] == "BUDGET_NOT_FOUND"


def test_remaining_budget_for_user_scope_is_unsupported(
    db,
    employee_u001_scope,
):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "remaining_budget",
            "category": "Food",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "BUDGET_SCOPE_UNSUPPORTED"


def test_remaining_budget_admin_is_unsupported(db, admin_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "remaining_budget",
            "category": "Food",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        admin_scope,
    )

    assert result["status"] == "BUDGET_SCOPE_UNSUPPORTED"


def test_missing_budget_category(db, manager_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "remaining_budget",
            "category": "Travel",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
        },
        manager_scope,
    )

    assert result["status"] == "BUDGET_NOT_FOUND"


# ---------------------------------------------------------------------------
# Source-row evidence
# ---------------------------------------------------------------------------

def test_source_lookup_returns_matching_rows(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "source_lookup",
            "category": "Food",
            "currency": "INR",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["source_rows"] == ["EXP-001", "EXP-002"]
    assert len(result["result"]) == 2


def test_source_lookup_respects_user_scope(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "source_lookup",
        },
        employee_u001_scope,
    )

    assert result["status"] == "SUCCESS"

    returned_ids = {
        row["expense_id"]
        for row in result["result"]
    }

    assert returned_ids == {"EXP-001", "EXP-002"}


# ---------------------------------------------------------------------------
# Invalid intent / query
# ---------------------------------------------------------------------------

def test_unknown_intent(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        {
            "intent": "something_random",
        },
        employee_u001_scope,
    )

    assert result["status"] == "UNKNOWN_INTENT"
    assert result["result"] is None


def test_non_mapping_query(db, employee_u001_scope):
    from calculation.engine import run_calculation

    result = run_calculation(
        "not a query",
        employee_u001_scope,
    )

    assert result["status"] == "INVALID_QUERY"
    assert result["result"] is None


# ---------------------------------------------------------------------------
# Formula integration
# ---------------------------------------------------------------------------

def test_burn_rate_manager_with_budget(db):
    from calculation.engine import run_calculation

    # Create a CC-TECH manager so the budget can be resolved.
    scope = {
        "user_id": "U001",
        "role": "Manager",
        "scope_type": "cost_centre",
        "cost_centre": "CC-TECH",
    }

    result = run_calculation(
        {
            "intent": "burn_rate",
            "category": "Food",
            "date_range_start": "2026-09-01",
            "date_range_end": "2026-09-30",
            "currency": "INR",
        },
        scope,
    )

    assert result["status"] == "SUCCESS"
    assert result["result"] == 60.0
    assert result["currency"] == "INR"
    assert result["budget_amount"] == 5000
    assert result["spend"] == 3000