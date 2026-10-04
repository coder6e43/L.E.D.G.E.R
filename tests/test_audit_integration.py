"""Integration tests for L.E.D.G.E.R. Audit and Testing module.

Covers the complete end-to-end query flow:
    User -> Authentication -> RBAC -> Query Compiler -> Calculation -> Audit -> Response

Includes tests for all 14 required audit behaviors:
1. Successful query creates audit record.
2. Audit contains trusted user identity.
3. Audit contains correct scope.
4. Audit contains source rows.
5. Audit contains numeric result.
6. Access-denied query is logged appropriately.
7. Refused query is logged appropriately.
8. Clarification query is logged appropriately.
9. Passwords are never logged.
10. Client-provided scope cannot become trusted audit scope.
11. Audit record can be retrieved.
12. Recent audit records can be retrieved.
13. Query ID is unique.
14. Complete end-to-end query flow produces an audit trail with source-row traceability.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app, login_user, logout_user, run_authenticated_query
from audit.logger import get_audit_record, get_recent, log_query
from auth.session import get_current_user
from database.connection import get_connection


def _get_user_email(role="Manager"):
    """Helper to fetch a user email from the loaded test database."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT email FROM users WHERE role = ? ORDER BY user_id LIMIT 1", (role,)
        ).fetchone()
        return row["email"] if row else None


@pytest.fixture
def audit_db(tmp_path):
    """Isolated audit database path for testing."""
    return tmp_path / "data" / "audit.db"


# =============================================================================
# 1. Successful query creates audit record
# =============================================================================


def test_successful_query_creates_audit_record(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    result = run_authenticated_query(
        "How much did I spend on Food in September 2026?",
        db_path=audit_db,
    )

    assert result["status"] == "SUCCESS"
    assert "query_id" in result
    qid = result["query_id"]

    rec = get_audit_record(qid, db_path=audit_db)
    assert rec is not None
    assert rec["query_id"] == qid
    assert rec["execution_status"] == "SUCCESS"
    assert rec["user_id"] == user.user_id
    assert rec["timestamp"] is not None
    assert rec["latency_ms"] is not None and rec["latency_ms"] >= 0


# =============================================================================
# 2. Audit contains trusted user identity
# =============================================================================


def test_audit_contains_trusted_user_identity(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    # An attacker attempts to inject a different user_id
    result = run_authenticated_query(
        {
            "prompt": "How much did I spend on travel in September 2026?",
            "user_id": "U-ATTACKER-999",
        },
        db_path=audit_db,
    )

    assert result["status"] == "SUCCESS"
    qid = result["query_id"]
    rec = get_audit_record(qid, db_path=audit_db)

    # Must log the server-authenticated user_id, NEVER the injected identity
    assert rec["user_id"] == user.user_id
    assert rec["user_id"] != "U-ATTACKER-999"


# =============================================================================
# 3. Audit contains correct scope
# =============================================================================


def test_audit_contains_correct_scope(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None
    trusted_scope = user.cost_centre

    # Client tries to pass a different cost centre
    result = run_authenticated_query(
        {
            "prompt": "How much did I spend on software in September 2026?",
            "cost_centre": "CC-UNAUTHORIZED",
            "user_scope": "CC-UNAUTHORIZED",
        },
        db_path=audit_db,
    )

    assert result["status"] == "SUCCESS"
    qid = result["query_id"]
    rec = get_audit_record(qid, db_path=audit_db)

    assert rec["scope"] == trusted_scope
    assert rec["scope"] != "CC-UNAUTHORIZED"
    assert rec["applied_filters"]["cost_centre"] == trusted_scope


# =============================================================================
# 4. Audit contains source rows
# =============================================================================


def test_audit_contains_source_rows(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    result = run_authenticated_query(
        "How much did I spend on Food in September 2026?",
        db_path=audit_db,
    )

    assert result["status"] == "SUCCESS"
    source_rows = result.get("source_rows")
    assert isinstance(source_rows, list)
    assert len(source_rows) > 0

    rec = get_audit_record(result["query_id"], db_path=audit_db)
    assert rec["source_row_ids"] == source_rows

    # Verify that every source row exists in the SQLite expenses table
    with get_connection() as conn:
        placeholders = ",".join("?" for _ in source_rows)
        rows = conn.execute(
            f"SELECT expense_id, cost_centre, category FROM expenses WHERE expense_id IN ({placeholders})",
            source_rows,
        ).fetchall()

    assert len(rows) == len(source_rows)
    for r in rows:
        assert r["cost_centre"] == user.cost_centre
        assert r["category"] == "Food"


# =============================================================================
# 5. Audit contains numeric result
# =============================================================================


def test_audit_contains_numeric_result(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    result = run_authenticated_query(
        "How much did I spend on Food in September 2026?",
        db_path=audit_db,
    )

    assert result["status"] == "SUCCESS"
    expected_result = result["result"]
    assert isinstance(expected_result, (int, float))
    assert not isinstance(expected_result, bool)

    rec = get_audit_record(result["query_id"], db_path=audit_db)
    assert rec["numeric_result"] == pytest.approx(float(expected_result), rel=1e-5)


# =============================================================================
# 6. Access-denied query is logged appropriately
# =============================================================================


def test_access_denied_query_is_logged_appropriately(sample_database, audit_db):
    # Employee has user scope, which calculation engine currently does not support
    user = login_user(_get_user_email("Employee"), "Password123!")
    assert user is not None

    result = run_authenticated_query(
        "How much did I spend on food in September 2026?",
        db_path=audit_db,
    )

    assert result["status"] in {"ACCESS_DENIED", "SCOPE_UNSUPPORTED"}
    assert result["result"] is None

    # Verify an ACCESS_DENIED audit record was created for the authenticated user
    records = get_recent(limit=5, db_path=audit_db)
    assert len(records) > 0
    rec = records[0]
    assert rec["user_id"] == user.user_id
    assert rec["execution_status"] == "ACCESS_DENIED"
    assert rec["numeric_result"] is None
    # Source rows must be None (never fabricated)
    assert rec["source_row_ids"] is None


# =============================================================================
# 7. Refused query is logged appropriately
# =============================================================================


def test_refused_query_is_logged_appropriately(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    # Future prediction prompt is rejected by Query Compiler
    result = run_authenticated_query(
        "How much will I spend on travel next month?",
        db_path=audit_db,
    )

    assert result["status"] == "REFUSED"
    assert result["result"] is None
    qid = result["query_id"]

    rec = get_audit_record(qid, db_path=audit_db)
    assert rec is not None
    assert rec["execution_status"] == "REFUSED"
    assert rec["numeric_result"] is None
    assert rec["source_row_ids"] is None
    assert rec["user_id"] == user.user_id


# =============================================================================
# 8. Clarification query is logged appropriately
# =============================================================================


def test_clarification_query_is_logged_appropriately(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    # Remaining budget prompt without category requires clarification
    result = run_authenticated_query(
        "How much budget is left?",
        db_path=audit_db,
    )

    assert result["status"] == "CLARIFY"
    assert result["result"] is None
    qid = result["query_id"]

    rec = get_audit_record(qid, db_path=audit_db)
    assert rec is not None
    assert rec["execution_status"] == "CLARIFY"
    assert rec["numeric_result"] is None
    assert rec["source_row_ids"] is None
    assert rec["user_id"] == user.user_id


# =============================================================================
# 9. Passwords are never logged
# =============================================================================


def test_passwords_are_never_logged_in_audit(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    secret_password = "SuperSecretPassword123!"
    secret_hash = "$2b$12$e8k...simulatedhash..."

    # Test prompt containing credentials
    result1 = run_authenticated_query(
        f"How much did I spend on Food? password is {secret_password}",
        db_path=audit_db,
    )
    assert "query_id" in result1
    rec1 = get_audit_record(result1["query_id"], db_path=audit_db)

    assert secret_password not in rec1["raw_prompt"]
    assert "[REDACTED]" in rec1["raw_prompt"]
    assert secret_password not in json.dumps(rec1["parsed_json"] or {})

    # Test dictionary containing password & password_hash fields
    result2 = run_authenticated_query(
        {
            "intent": "sum_expenses",
            "category": "Food",
            "password": secret_password,
            "password_hash": secret_hash,
            "secret": "topsecret",
        },
        db_path=audit_db,
    )
    assert "query_id" in result2
    rec2 = get_audit_record(result2["query_id"], db_path=audit_db)

    # Whitelist sanitizer must drop password, password_hash, and secret
    raw_prompt2 = rec2["raw_prompt"]
    assert secret_password not in raw_prompt2
    assert secret_hash not in raw_prompt2
    assert "password" not in raw_prompt2.lower()

    parsed_json_str = json.dumps(rec2["parsed_json"] or {})
    assert secret_password not in parsed_json_str
    assert secret_hash not in parsed_json_str
    assert "password" not in parsed_json_str.lower()


# =============================================================================
# 10. Client-provided scope cannot become trusted audit scope
# =============================================================================


def test_client_provided_scope_cannot_become_trusted_audit_scope(
    sample_database, audit_db
):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None
    assert user.cost_centre == "CC-TECH"

    result = run_authenticated_query(
        {
            "intent": "sum_expenses",
            "category": "Food",
            "cost_centre": "CC-MARKETING",  # Attacker tries to impersonate CC-MARKETING
            "user_scope": "CC-SALES",
        },
        db_path=audit_db,
    )

    # If the user_scope conflicts with authorized scope, it fails or uses authorized scope
    if result["status"] == "SUCCESS":
        rec = get_audit_record(result["query_id"], db_path=audit_db)
        assert rec["scope"] == "CC-TECH"
        assert rec["scope"] != "CC-MARKETING"
        assert rec["scope"] != "CC-SALES"
    else:
        # Access denied or user scope conflict
        assert result["status"] in {"USER_SCOPE_CONFLICT", "ACCESS_DENIED", "REFUSED"}


# =============================================================================
# 11. Audit record can be retrieved
# =============================================================================


def test_audit_record_can_be_retrieved(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    result = run_authenticated_query(
        "Total travel spend in September 2026",
        db_path=audit_db,
    )
    qid = result["query_id"]

    rec = get_audit_record(qid, db_path=audit_db)
    assert rec is not None
    assert rec["query_id"] == qid
    assert rec["user_id"] == user.user_id
    assert rec["scope"] == user.cost_centre
    assert isinstance(rec["applied_filters"], dict)
    assert isinstance(rec["source_row_ids"], list)

    # Non-existent query ID must return None
    assert get_audit_record("non-existent-uuid-1234", db_path=audit_db) is None


# =============================================================================
# 12. Recent audit records can be retrieved
# =============================================================================


def test_recent_audit_records_can_be_retrieved(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    prompts = [
        "How much did I spend on Food in September 2026?",
        "Total travel spend in September 2026",
        "What did we spend on Software in September 2026?",
    ]

    for p in prompts:
        res = run_authenticated_query(p, db_path=audit_db)
        assert res["status"] == "SUCCESS"

    recent = get_recent(limit=2, db_path=audit_db)
    assert len(recent) == 2

    all_three = get_recent(limit=10, db_path=audit_db)
    assert len(all_three) >= 3
    # Check descending order: the last query executed should be first
    assert "Software" in all_three[0]["raw_prompt"]


# =============================================================================
# 13. Query ID is unique
# =============================================================================


def test_query_id_is_unique(sample_database, audit_db):
    user = login_user(_get_user_email("Manager"), "Password123!")
    assert user is not None

    query_ids = []
    for _ in range(15):
        res = run_authenticated_query(
            "How much did I spend on Food in September 2026?",
            db_path=audit_db,
        )
        assert res["status"] == "SUCCESS"
        query_ids.append(res["query_id"])

    assert len(query_ids) == 15
    # All IDs must be unique
    assert len(set(query_ids)) == 15


# =============================================================================
# 14. Complete end-to-end query flow produces an audit trail + traceability
# =============================================================================


def test_complete_end_to_end_flow_and_traceability(sample_database, audit_db):
    """End-to-End Query Flow:
        User -> Authentication -> RBAC -> Query Compiler -> Calculation -> Audit -> Response

    Traceability:
        numeric result -> source_row_ids -> exact database records
    """
    # 1. Authentication
    email = _get_user_email("Manager")
    user = login_user(email, "Password123!")
    assert user is not None
    assert get_current_user() is user

    # 2. End-to-end natural language execution
    prompt = "How much did I spend on Food in September 2026?"
    result = run_authenticated_query(prompt, db_path=audit_db)

    # 3. Verify Response
    assert result["status"] == "SUCCESS"
    assert result["result"] is not None
    assert result["currency"] == "INR"
    assert len(result["source_rows"]) > 0
    qid = result["query_id"]

    # 4. Verify Audit Record
    rec = get_audit_record(qid, db_path=audit_db)
    assert rec is not None
    assert rec["query_id"] == qid
    assert rec["user_id"] == user.user_id
    assert rec["scope"] == user.cost_centre
    assert rec["execution_status"] == "SUCCESS"
    assert rec["numeric_result"] == result["result"]
    assert rec["source_row_ids"] == result["source_rows"]

    # 5. Full Traceability Verification:
    # numeric result -> source_row_ids -> exact database records
    source_ids = rec["source_row_ids"]
    placeholders = ",".join("?" for _ in source_ids)

    with get_connection() as conn:
        db_rows = conn.execute(
            f"SELECT expense_id, cost_centre, category, amount, date FROM expenses WHERE expense_id IN ({placeholders})",
            source_ids,
        ).fetchall()

    assert len(db_rows) == len(source_ids)

    # Verify that all source rows conform to the authorized cost centre and category
    for row in db_rows:
        assert row["cost_centre"] == rec["scope"]
        assert row["category"] == "Food"
        assert "2026-09-01" <= row["date"] <= "2026-09-30"

    # Verify the sum of exact database records matches the audited numeric result
    db_sum = sum(row["amount"] for row in db_rows)
    assert db_sum == pytest.approx(rec["numeric_result"], rel=1e-5)
    assert db_sum == pytest.approx(result["result"], rel=1e-5)

    logout_user()
    assert get_current_user() is None


# =============================================================================
# HTTP API Integration: Audit Retrieval Endpoints
# =============================================================================


def test_http_audit_endpoints(sample_database):
    # 1. Manager runs a financial query (has query:ask and expense:view_cost_centre)
    mgr = login_user(_get_user_email("Manager"), "Password123!")
    assert mgr is not None

    res = run_authenticated_query("Total travel spend in September 2026")
    assert res["status"] == "SUCCESS"
    qid = res["query_id"]

    client = TestClient(app)

    # 2. Manager attempts to view audit logs -> 403 Forbidden (only Admin has audit:view)
    mgr_resp = client.get(f"/audit/{qid}")
    assert mgr_resp.status_code == 403

    # 3. Unauthenticated request -> 401 Unauthorized
    logout_user()
    unauth_resp = client.get(f"/audit/{qid}")
    assert unauth_resp.status_code == 401

    # 4. Admin logs in -> 200 OK (Admin has audit:view permission)
    admin = login_user(_get_user_email("Admin"), "Password123!")
    assert admin is not None

    admin_resp = client.get(f"/audit/{qid}")
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    assert data["query_id"] == qid
    assert data["execution_status"] == "SUCCESS"

    # Test recent endpoint for Admin
    recent_resp = client.get("/audit/recent?limit=5")
    assert recent_resp.status_code == 200
    recent_data = recent_resp.json()
    assert isinstance(recent_data, list)
    assert len(recent_data) >= 1

