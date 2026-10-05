"""Security and Auth/RBAC boundary tests for the Query Compiler."""

from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from query import api
from query.api import CompileQueryRequest
from query.compiler import compile_query
from query.schema import AuthorizationScope, ScopeType, Status


def employee_scope():
    return AuthorizationScope(
        user_id="U-001",
        role="Employee",
        scope_type=ScopeType.user,
        scope_user_id="U-001",
    )


def manager_scope():
    return AuthorizationScope(
        user_id="U-002",
        role="Manager",
        scope_type=ScopeType.cost_centre,
        cost_centre="CC-TECH",
    )


def admin_scope():
    return AuthorizationScope(
        user_id="U-003",
        role="Admin",
        scope_type=ScopeType.organization,
    )


def test_client_scope_field_is_not_accepted():
    request = CompileQueryRequest.model_validate(
        {"prompt": "How much did I spend this month?"}
    )
    assert request.prompt == "How much did I spend this month?"

    try:
        CompileQueryRequest.model_validate(
            {
                "prompt": "How much did I spend this month?",
                "user_scope": "CC-ATTACKER",
            }
        )
    except ValueError:
        pass
    else:
        raise AssertionError("client user_scope must be rejected")


def test_employee_scope_is_preserved():
    result = compile_query(
        "How much did I spend on food this month?",
        scope=employee_scope(),
        current_date=date(2026, 10, 4),
    )
    assert result.status == Status.SUCCESS
    assert result.query.scope == employee_scope()


def test_manager_cost_centre_scope_is_preserved():
    result = compile_query(
        "How much did I spend on travel this month?",
        scope=manager_scope(),
        current_date=date(2026, 10, 4),
    )
    assert result.status == Status.SUCCESS
    assert result.query.scope == manager_scope()


def test_admin_organization_scope_is_preserved():
    result = compile_query(
        "How much did I spend on software this month?",
        scope=admin_scope(),
        current_date=date(2026, 10, 4),
    )
    assert result.status == Status.SUCCESS
    assert result.query.scope == admin_scope()


def test_scope_does_not_convert_user_to_cost_centre():
    scope = employee_scope()
    result = compile_query(
        "How much did I spend this month?",
        scope=scope,
        current_date=date(2026, 10, 4),
    )
    assert result.status == Status.SUCCESS
    assert result.query.scope.scope_type == ScopeType.user
    assert result.query.scope.cost_centre is None


def test_scope_does_not_convert_organization_to_cost_centre():
    scope = admin_scope()
    result = compile_query(
        "How much did I spend this month?",
        scope=scope,
        current_date=date(2026, 10, 4),
    )
    assert result.status == Status.SUCCESS
    assert result.query.scope.scope_type == ScopeType.organization
    assert result.query.scope.cost_centre is None


def test_api_rejects_client_scope_override():
    app = FastAPI()
    app.include_router(api.router)
    trusted = manager_scope()
    app.dependency_overrides[api.get_trusted_scope] = lambda: trusted

    captured = {}

    def fake_compile_query(prompt, scope, current_date=None):
        captured["prompt"] = prompt
        captured["scope"] = scope
        captured["current_date"] = current_date
        return {
            "status": "SUCCESS",
            "query": {
                "intent": "sum_expenses",
                "scope": scope.model_dump(),
                "category": None,
                "date_range_start": date(2026, 10, 1),
                "date_range_end": date(2026, 10, 4),
                "limit": None,
                "currency": "INR",
            },
        }

    original = api.compile_query
    api.compile_query = fake_compile_query
    try:
        client = TestClient(app)
        response = client.post(
            "/query/compile",
            json={
                "prompt": "How much did I spend this month?",
                "user_scope": "CC-ATTACKER",
            },
        )
        assert response.status_code == 422
    finally:
        api.compile_query = original
        app.dependency_overrides.clear()


def test_api_passes_trusted_scope_downstream():
    app = FastAPI()
    app.include_router(api.router)
    trusted = manager_scope()
    app.dependency_overrides[api.get_trusted_scope] = lambda: trusted

    captured = {}

    def fake_compile_query(prompt, scope, current_date=None):
        captured["prompt"] = prompt
        captured["scope"] = scope
        captured["current_date"] = current_date
        return {
            "status": "SUCCESS",
            "query": {
                "intent": "sum_expenses",
                "scope": scope.model_dump(),
                "category": None,
                "date_range_start": date(2026, 10, 1),
                "date_range_end": date(2026, 10, 4),
                "limit": None,
                "currency": "INR",
            },
        }

    original = api.compile_query
    api.compile_query = fake_compile_query
    try:
        client = TestClient(app)
        response = client.post(
            "/query/compile",
            json={"prompt": "How much did I spend this month?"},
        )
        assert response.status_code == 200
        assert captured["scope"] == trusted
    finally:
        api.compile_query = original
        app.dependency_overrides.clear()



def test_client_cannot_supply_any_authorization_field():
    forbidden_fields = [
        "scope",
        "role",
        "cost_centre",
        "organization",
        "scope_type",
        "scope_user_id",
    ]

    for field in forbidden_fields:
        try:
            CompileQueryRequest.model_validate(
                {
                    "prompt": "How much did I spend this month?",
                    field: "attacker-controlled-value",
                }
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"client field {field!r} must be rejected")


def test_api_passes_employee_scope_unchanged():
    app = FastAPI()
    app.include_router(api.router)
    trusted = employee_scope()
    app.dependency_overrides[api.get_trusted_scope] = lambda: trusted

    captured = {}

    def fake_compile_query(prompt, scope, current_date=None):
        captured["scope"] = scope
        return {
            "status": "SUCCESS",
            "query": {
                "intent": "sum_expenses",
                "scope": scope.model_dump(),
                "category": None,
                "date_range_start": date(2026, 10, 1),
                "date_range_end": date(2026, 10, 4),
                "limit": None,
                "currency": "INR",
            },
        }

    original = api.compile_query
    api.compile_query = fake_compile_query
    try:
        response = TestClient(app).post(
            "/query/compile",
            json={"prompt": "How much did I spend this month?"},
        )
        assert response.status_code == 200
        assert captured["scope"] == trusted
    finally:
        api.compile_query = original
        app.dependency_overrides.clear()


def test_api_passes_admin_scope_unchanged():
    app = FastAPI()
    app.include_router(api.router)
    trusted = admin_scope()
    app.dependency_overrides[api.get_trusted_scope] = lambda: trusted

    captured = {}

    def fake_compile_query(prompt, scope, current_date=None):
        captured["scope"] = scope
        return {
            "status": "SUCCESS",
            "query": {
                "intent": "sum_expenses",
                "scope": scope.model_dump(),
                "category": None,
                "date_range_start": date(2026, 10, 1),
                "date_range_end": date(2026, 10, 4),
                "limit": None,
                "currency": "INR",
            },
        }

    original = api.compile_query
    api.compile_query = fake_compile_query
    try:
        response = TestClient(app).post(
            "/query/compile",
            json={"prompt": "How much did I spend this month?"},
        )
        assert response.status_code == 200
        assert captured["scope"] == trusted
    finally:
        api.compile_query = original
        app.dependency_overrides.clear()
