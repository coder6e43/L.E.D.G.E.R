"""Authentication, request session, and authorization helpers for LEDGER."""

from auth.authentication import AuthenticatedUser, authenticate_user
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
    "authorize_cost_centre",
    "authorize_role",
    "get_authorized_cost_centre",
    "get_authorized_scope",
    "has_permission",
    "require_permission",
    "resolve_authorized_scope",
    "get_current_user",
    "is_authenticated",
    "logout",
    "set_authenticated_user",
    "validate_role",
]
