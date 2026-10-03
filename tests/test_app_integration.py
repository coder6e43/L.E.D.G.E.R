from pathlib import Path

import json

from audit.logger import get_recent
from auth.session import get_current_user
from app import login_user, logout_user, run_authenticated_query
from database.connection import get_connection


def _sample_user_email(role="Manager"):
    with get_connection() as conn:
        return conn.execute(
            "SELECT email FROM users WHERE role = ? ORDER BY user_id LIMIT 1", (role,)
        ).fetchone()["email"]


def test_structured_query_requires_authenticated_session(sample_database):
    logout_user()
    result = run_authenticated_query({"intent": "expense_count"})
    assert result["status"] == "ACCESS_DENIED"
    assert result["result"] is None
    assert not (Path(sample_database["path"]).parent / "audit.db").exists()


def test_login_query_scope_and_audit_use_trusted_identity(sample_database):
    user = login_user(_sample_user_email(), "Password123!")
    assert user is not None
    assert get_current_user() is user

    with get_connection() as conn:
        other_scope = conn.execute(
            "SELECT cost_centre FROM users WHERE cost_centre != ? LIMIT 1",
            (user.cost_centre,),
        ).fetchone()["cost_centre"]

    result = run_authenticated_query(
        {
            "intent": "expense_count",
            "cost_centre": other_scope,
            "role": "Admin",
            "password": "Password123!",
        }
    )
    assert result["status"] == "SUCCESS"
    assert result["filters"]["cost_centre"] == user.cost_centre

    if result["source_rows"]:
        placeholders = ",".join("?" for _ in result["source_rows"])
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT cost_centre FROM expenses WHERE expense_id IN ({placeholders})",
                result["source_rows"],
            ).fetchall()
    else:
        rows = []
    assert all(row["cost_centre"] == user.cost_centre for row in rows)

    record = get_recent(db_path=Path(sample_database["path"]).parent / "audit.db")[0]
    assert record["user_id"] == user.user_id
    assert record["scope"] == user.cost_centre
    parsed_audit = json.loads(record["parsed_json"])
    assert parsed_audit["authenticated_role"] == user.role
    assert "role" not in parsed_audit["query"]
    assert "password" not in record["raw_prompt"].lower()
    assert "Password123!" not in record["raw_prompt"]
    assert json.loads(record["source_row_ids"]) == result["source_rows"]

    logout_user()
    assert get_current_user() is None


def test_failed_login_clears_any_existing_identity(sample_database):
    assert login_user(_sample_user_email(), "Password123!") is not None
    assert login_user(_sample_user_email(), "wrong password") is None
    assert get_current_user() is None


def test_app_fails_closed_when_engine_cannot_represent_employee_scope(sample_database):
    user = login_user(_sample_user_email("Employee"), "Password123!")
    assert user is not None
    result = run_authenticated_query({"intent": "expense_count"})
    assert result["status"] == "SCOPE_UNSUPPORTED"
    assert result["result"] is None


def test_app_fails_closed_when_engine_cannot_represent_admin_scope(sample_database):
    user = login_user(_sample_user_email("Admin"), "Password123!")
    assert user is not None
    result = run_authenticated_query({"intent": "expense_count"})
    assert result["status"] == "SCOPE_UNSUPPORTED"
    assert result["result"] is None
