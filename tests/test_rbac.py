import pytest

from auth.authentication import AuthenticatedUser
from auth.rbac import (
    PERMISSIONS,
    ROLE_PERMISSIONS,
    AuthorizationError,
    authorize_cost_centre,
    authorize_cost_centre_access_management,
    authorize_expense_creation,
    authorize_role,
    authorize_role_assignment,
    get_authorized_cost_centre,
    get_authorized_scope,
    has_permission,
    require_permission,
    validate_role,
)

ROLES = ("Employee", "Manager", "Admin")


def make_user(role="Manager", user_id="U001", cost_centre="CC-TECH"):
    return AuthenticatedUser._from_database(
        {
            "user_id": user_id,
            "name": "Test",
            "email": "test@example.com",
            "role": role,
            "cost_centre": cost_centre,
        }
    )


@pytest.mark.parametrize("role", ROLES)
def test_supported_roles(role):
    assert validate_role(role) == role


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        validate_role("Root")


def test_final_permission_matrix_is_centralized_and_exact():
    own = {"query:ask", "expense:view_own", "expense:create_own"}
    manager = own | {
        "expense:view_cost_centre",
        "budget:view_cost_centre",
        "trend:view_cost_centre",
    }
    admin = manager | {
        "audit:view",
        "report:export",
        "cost_centre:view_all",
        "user:manage",
        "role:assign",
        "cost_centre:manage_access",
    }
    assert ROLE_PERMISSIONS == {
        "Employee": own,
        "Manager": manager,
        "Admin": admin,
    }
    assert set().union(*ROLE_PERMISSIONS.values()) == PERMISSIONS


@pytest.mark.parametrize("role", ROLES)
def test_undefined_permission_is_denied(role):
    user = make_user(role)
    assert not has_permission(user, "permission:not-defined")
    with pytest.raises(AuthorizationError):
        require_permission(user, "permission:not-defined")


@pytest.mark.parametrize("role", ROLES)
def test_query_and_own_expense_permissions(role):
    user = make_user(role)
    assert has_permission(user, "query:ask")
    assert has_permission(user, "expense:view_own")
    assert has_permission(user, "expense:create_own")


def test_employee_cannot_perform_manager_or_admin_operations():
    employee = make_user("Employee")
    for permission in (
        "expense:view_cost_centre", "budget:view_cost_centre", "trend:view_cost_centre",
        "audit:view", "report:export", "cost_centre:view_all", "user:manage",
        "role:assign", "cost_centre:manage_access",
    ):
        assert not has_permission(employee, permission), permission


def test_manager_can_view_only_assigned_cost_centre_operations():
    manager = make_user("Manager")
    for permission in (
        "expense:view_cost_centre", "budget:view_cost_centre", "trend:view_cost_centre"
    ):
        assert has_permission(manager, permission)
    for permission in (
        "audit:view", "report:export", "cost_centre:view_all", "user:manage",
        "role:assign", "cost_centre:manage_access",
    ):
        assert not has_permission(manager, permission), permission


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("Employee", {"user_id": "U001", "role": "Employee", "scope_type": "user", "scope_user_id": "U001"}),
        ("Manager", {"user_id": "U001", "role": "Manager", "scope_type": "cost_centre", "cost_centre": "CC-TECH"}),
        ("Admin", {"user_id": "U001", "role": "Admin", "scope_type": "organization"}),
    ],
)
def test_authorized_scope_is_role_derived(role, expected):
    assert get_authorized_scope(make_user(role)) == expected


def test_employee_scope_is_only_own_user_data():
    employee = make_user("Employee")
    assert get_authorized_scope(employee, requested_user_id="U001")["scope_user_id"] == "U001"
    with pytest.raises(AuthorizationError):
        get_authorized_scope(employee, requested_user_id="U999")
    with pytest.raises(AuthorizationError):
        get_authorized_scope(employee, requested_cost_centre="CC-TECH")


def test_manager_cannot_expand_scope_to_another_cost_centre():
    manager = make_user("Manager")
    assert get_authorized_cost_centre(manager) == "CC-TECH"
    assert authorize_cost_centre(manager) == "CC-TECH"
    assert authorize_cost_centre(manager, "CC-TECH") == "CC-TECH"
    with pytest.raises(AuthorizationError):
        authorize_cost_centre(manager, "CC-FINANCE")
    with pytest.raises(AuthorizationError):
        get_authorized_scope(manager, requested_cost_centre="CC-FINANCE")


def test_employee_and_admin_do_not_get_misrepresented_as_single_cost_centre():
    for role in ("Employee", "Admin"):
        with pytest.raises(AuthorizationError):
            get_authorized_cost_centre(make_user(role))
    with pytest.raises(AuthorizationError):
        authorize_cost_centre(make_user("Employee"), "CC-TECH")


def test_admin_can_authorize_any_specific_cost_centre_filter():
    admin = make_user("Admin")
    assert has_permission(admin, "cost_centre:view_all")
    assert authorize_cost_centre(admin, "CC-FINANCE") == "CC-FINANCE"
    with pytest.raises(AuthorizationError):
        authorize_cost_centre(admin)
    with pytest.raises(AuthorizationError):
        get_authorized_scope(admin, requested_cost_centre="CC-FINANCE")


def test_conflicting_role_override_is_denied_for_every_role():
    for role in ROLES:
        user = make_user(role)
        assert authorize_role(user) == role
        with pytest.raises(AuthorizationError):
            authorize_role(user, "Admin" if role != "Admin" else "Employee")
        with pytest.raises(AuthorizationError):
            get_authorized_scope(user, requested_role="Root")


def test_fabricated_identity_and_unauthenticated_context_fail_closed():
    with pytest.raises(AuthorizationError):
        get_authorized_scope({"user_id": "U001", "role": "Admin"})
    with pytest.raises(TypeError):
        AuthenticatedUser("U001", "Attacker", "x@example.com", "Admin", "CC-SALES")


def test_missing_scope_and_invalid_authenticated_role_fail_closed():
    user_without_scope = make_user("Employee", cost_centre=" ")
    with pytest.raises(AuthorizationError):
        authorize_expense_creation(user_without_scope)
    malformed_user = make_user("Root")
    with pytest.raises(AuthorizationError):
        get_authorized_scope(malformed_user)


@pytest.mark.parametrize("new_role", ROLES)
def test_admin_can_authorize_assigning_each_supported_role(new_role):
    assert authorize_role_assignment(make_user("Admin"), new_role, "U999") == new_role
    assert authorize_role_assignment(make_user("Admin"), new_role) == new_role


@pytest.mark.parametrize("role", ["Employee", "Manager"])
@pytest.mark.parametrize("new_role", ROLES)
def test_non_admin_cannot_assign_or_escalate_roles(role, new_role):
    actor = make_user(role)
    with pytest.raises(AuthorizationError):
        authorize_role_assignment(actor, new_role, actor.user_id)
    with pytest.raises(AuthorizationError):
        authorize_role_assignment(actor, new_role, "U999")


def test_role_assignment_rejects_unsupported_role_even_for_admin():
    with pytest.raises(ValueError):
        authorize_role_assignment(make_user("Admin"), "Root", "U999")


def test_only_admin_can_authorize_cost_centre_access_management():
    assert authorize_cost_centre_access_management(
        make_user("Admin"), "U999", "CC-FINANCE"
    ) is None
    for role in ("Employee", "Manager"):
        with pytest.raises(AuthorizationError):
            authorize_cost_centre_access_management(make_user(role), "U999", "CC-FINANCE")


@pytest.mark.parametrize("role", ROLES)
def test_future_expense_creation_is_limited_to_authenticated_owner(role):
    user = make_user(role)
    assert authorize_expense_creation(user) == {
        "user_id": "U001", "cost_centre": "CC-TECH"
    }
    with pytest.raises(AuthorizationError):
        authorize_expense_creation(user, requested_user_id="U999")
    with pytest.raises(AuthorizationError):
        authorize_expense_creation(user, requested_cost_centre="CC-FINANCE")
