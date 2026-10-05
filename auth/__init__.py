"""Authentication, request session, and authorization helpers for LEDGER."""

from auth.authentication import AuthenticatedUser, authenticate_user, load_session_user
from auth.rbac import (
    AuthorizationError,
    authorize_cost_centre,
    authorize_cost_centre_access_management,
    authorize_expense_creation,
    authorize_role,
    authorize_role_assignment,
    get_authorized_cost_centre,
    get_authorized_scope,
    has_permission,
    PERMISSIONS,
    require_permission,
    resolve_authorized_scope,
    ROLE_PERMISSIONS,
    validate_role,
)
from auth.session import (
    get_current_user,
    is_authenticated,
    logout,
    set_authenticated_user,
)

__all__ = [
    "AuthenticatedUser",
    "AuthorizationError",
    "authenticate_user",
    "load_session_user",
    "authorize_cost_centre",
    "authorize_cost_centre_access_management",
    "authorize_expense_creation",
    "authorize_role",
    "authorize_role_assignment",
    "get_authorized_cost_centre",
    "get_authorized_scope",
    "has_permission",
    "PERMISSIONS",
    "ROLE_PERMISSIONS",
    "require_permission",
    "resolve_authorized_scope",
    "get_current_user",
    "is_authenticated",
    "logout",
    "set_authenticated_user",
    "validate_role",
]
