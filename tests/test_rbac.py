import pytest

from auth.authentication import AuthenticatedUser
from auth.rbac import (
    AuthorizationError,
    authorize_cost_centre,
    get_authorized_cost_centre,
    has_permission,
    require_permission,
    resolve_authorized_scope,
    validate_role,
)


@pytest.fixture
def user():
    return AuthenticatedUser("U001", "Test", "test@example.com", "Manager", "CC-TECH")


@pytest.mark.parametrize("role", ["Manager", "Employee", "Admin"])
def test_allowed_roles(role):
    assert validate_role(role) == role


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        validate_role("Root")


def test_permissions_are_denied_until_policy_is_configured(user):
    assert not has_permission(user, "expense.read")
    with pytest.raises(AuthorizationError):
        require_permission(user, "expense.read")


def test_scope_comes_from_authenticated_identity(user):
    assert get_authorized_cost_centre(user) == "CC-TECH"
    assert resolve_authorized_scope(user) == {
        "user_id": "U001", "role": "Manager", "cost_centre": "CC-TECH"
    }


def test_other_cost_centre_is_denied(user):
    with pytest.raises(AuthorizationError):
        authorize_cost_centre(user, "CC-SALES")


def test_same_cost_centre_is_allowed(user):
    assert authorize_cost_centre(user, "CC-TECH") == "CC-TECH"


def test_frontend_role_or_scope_mapping_cannot_be_used_as_identity():
    with pytest.raises(AuthorizationError):
        get_authorized_cost_centre({"role": "Admin", "cost_centre": "CC-SALES"})

