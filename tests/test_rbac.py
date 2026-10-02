import pytest

from auth.authentication import AuthenticatedUser
from auth.rbac import (
    AuthorizationError,
    authorize_cost_centre,
    authorize_role,
    get_authorized_cost_centre,
    get_authorized_scope,
    has_permission,
    require_permission,
    resolve_authorized_scope,
    validate_role,
)


@pytest.fixture
def user():
    return AuthenticatedUser._from_database(
        {"user_id": "U001", "name": "Test", "email": "test@example.com",
         "role": "Manager", "cost_centre": "CC-TECH"}
    )


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
    assert get_authorized_scope(user) == resolve_authorized_scope(user)


def test_other_cost_centre_is_denied(user):
    with pytest.raises(AuthorizationError):
        authorize_cost_centre(user, "CC-SALES")


def test_role_override_is_denied_and_database_role_is_preserved(user):
    assert authorize_role(user) == "Manager"
    with pytest.raises(AuthorizationError):
        authorize_role(user, "Admin")
    with pytest.raises(AuthorizationError):
        get_authorized_scope(user, requested_role="Admin")
    assert get_authorized_scope(user)["role"] == "Manager"


def test_scope_override_is_denied_by_public_interface(user):
    with pytest.raises(AuthorizationError):
        get_authorized_scope(user, requested_cost_centre="CC-SALES")


def test_same_cost_centre_is_allowed(user):
    assert authorize_cost_centre(user, "CC-TECH") == "CC-TECH"


def test_frontend_role_or_scope_mapping_cannot_be_used_as_identity():
    with pytest.raises(AuthorizationError):
        get_authorized_cost_centre({"role": "Admin", "cost_centre": "CC-SALES"})


def test_fabricated_authenticated_user_is_denied():
    with pytest.raises(TypeError):
        AuthenticatedUser("U001", "Attacker", "x@example.com", "Admin", "CC-SALES")
