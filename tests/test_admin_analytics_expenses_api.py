"""Integration coverage for new database-backed dashboard APIs."""

from fastapi.testclient import TestClient

from app import app
from database.connection import get_connection


def _account(role: str) -> dict[str, str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, email, cost_centre FROM users WHERE role = ? ORDER BY user_id LIMIT 1",
            (role,),
        ).fetchone()
    return dict(row)


def _client_for(role: str) -> tuple[TestClient, dict[str, str]]:
    account = _account(role)
    client = TestClient(app)
    response = client.post("/auth/login", json={"email": account["email"], "password": "Password123!"})
    assert response.status_code == 200
    return client, account


def test_analytics_is_available_and_admin_api_is_role_protected(sample_database):
    employee, account = _client_for("Employee")
    response = employee.get("/analytics/overview")
    assert response.status_code == 200
    assert response.json()["scope"]["scope_type"] == "user"
    assert response.json()["expense_count"] >= 0
    assert employee.get("/admin/users").status_code == 403

    manager, manager_account = _client_for("Manager")
    manager_overview = manager.get("/analytics/overview").json()
    assert manager_overview["scope"]["scope_type"] == "cost_centre"
    assert manager.get("/admin/users").status_code == 403
    with get_connection() as conn:
        expected_manager_count = conn.execute(
            "SELECT COUNT(*) AS count FROM expenses WHERE cost_centre = ?",
            (manager_account["cost_centre"],),
        ).fetchone()["count"]
        organization_count = conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]
    assert manager_overview["expense_count"] == expected_manager_count

    admin, _ = _client_for("Admin")
    admin_overview = admin.get("/analytics/overview").json()
    assert admin_overview["scope"]["scope_type"] == "organization"
    assert admin_overview["expense_count"] == organization_count
    summary = admin.get("/admin/summary")
    assert summary.status_code == 200
    assert summary.json()["user_count"] == 110
    users = admin.get("/admin/users", params={"search": account["email"]})
    assert users.status_code == 200 and len(users.json()) == 1
    assert "password_hash" not in users.json()[0]


def test_admin_creates_and_updates_database_backed_user(sample_database):
    client, _ = _client_for("Admin")
    options = client.get("/admin/options").json()
    centre = options["cost_centres"][0]
    payload = {"name": "Integration Check", "email": "integration.check@example.test", "password": "Long-Test-Password-123", "role": "Employee", "cost_centre": centre}
    created = client.post("/admin/users", json=payload)
    assert created.status_code == 201, created.text
    user = created.json()
    assert user["email"] == payload["email"] and "password_hash" not in user
    assert client.patch(f"/admin/users/{user['user_id']}/role", json={"role": "Manager"}).json()["role"] == "Manager"
    other_centre = next((item for item in options["cost_centres"] if item != centre), centre)
    assert client.patch(f"/admin/users/{user['user_id']}/cost-centre", json={"cost_centre": other_centre}).json()["cost_centre"] == other_centre
    listed = client.get("/admin/users", params={"search": payload["email"]})
    assert listed.status_code == 200 and listed.json()[0]["role"] == "Manager"
    assert listed.json()[0]["cost_centre"] == other_centre
    with get_connection() as conn:
        row = conn.execute("SELECT role, cost_centre, password_hash FROM users WHERE user_id = ?", (user["user_id"],)).fetchone()
    assert row["role"] == "Manager" and row["cost_centre"] == other_centre
    assert row["password_hash"] != payload["password"]
    login = TestClient(app).post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200 and login.json()["role"] == "Manager"


def test_expense_creation_uses_session_identity_and_rejects_spoofed_scope(sample_database):
    client, account = _client_for("Employee")
    before = client.get("/analytics/overview").json()["expense_count"]
    invalid = client.post("/expenses", json={"category": "Food", "amount": 42, "currency": "INR", "date": "2026-09-01", "user_id": "U-OTHER", "role": "Admin", "cost_centre": "Other"})
    assert invalid.status_code == 422
    created = client.post("/expenses", json={"category": "Food", "amount": 42, "currency": "INR", "date": "2026-09-01", "description": "Test expense"})
    assert created.status_code == 201, created.text
    assert created.json()["user_id"] == account["user_id"]
    assert created.json()["cost_centre"] == account["cost_centre"]
    with get_connection() as conn:
        row = conn.execute("SELECT user_id, cost_centre FROM expenses WHERE expense_id = ?", (created.json()["expense_id"],)).fetchone()
    assert row["user_id"] == account["user_id"] and row["cost_centre"] == account["cost_centre"]
    assert client.get("/analytics/overview").json()["expense_count"] == before + 1


def test_google_oauth_is_disabled_without_configuration(sample_database, monkeypatch):
    for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
        monkeypatch.delenv(key, raising=False)
    client = TestClient(app)
    assert client.get("/auth/google/status").json() == {"enabled": False}
    assert client.get("/auth/google/login").status_code == 503
