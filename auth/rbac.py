"""Fail-closed role and cost-centre authorization helpers for LEDGER."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from auth.authentication import AuthenticatedUser, VALID_ROLES

# Policy is centralized here. Permissions outside this explicit matrix are
# denied by default; these identifiers authorize operations, not data scope.
PERMISSIONS = frozenset(
    {
        "query:ask",
        "expense:view_own",
        "expense:create_own",
        "expense:view_cost_centre",
        "budget:view_cost_centre",
        "trend:view_cost_centre",
        "audit:view",
        "report:export",
        "cost_centre:view_all",
        "user:manage",
        "role:assign",
        "cost_centre:manage_access",
    }
)

_OWN_PERMISSIONS = frozenset(
    {"query:ask", "expense:view_own", "expense:create_own"}
)
_COST_CENTRE_PERMISSIONS = frozenset(
    {"expense:view_cost_centre", "budget:view_cost_centre", "trend:view_cost_centre"}
)
_ADMIN_PERMISSIONS = frozenset(
    {
        "audit:view",
        "report:export",
        "cost_centre:view_all",
        "user:manage",
        "role:assign",
        "cost_centre:manage_access",
    }
)

ROLE_PERMISSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "Employee": _OWN_PERMISSIONS,
        "Manager": _OWN_PERMISSIONS | _COST_CENTRE_PERMISSIONS,
        "Admin": _OWN_PERMISSIONS | _COST_CENTRE_PERMISSIONS | _ADMIN_PERMISSIONS,
    }
)


class AuthorizationError(PermissionError):
    """Raised when an identity or requested scope is not authorized."""


def validate_role(role: str) -> str:
    """Return a recognized database role or reject it."""
    if not isinstance(role, str) or role not in VALID_ROLES:
        raise ValueError("Invalid role.")
    return role


def has_permission(user: AuthenticatedUser, permission: str) -> bool:
    """Check an explicitly configured role permission; default to deny."""
    _require_authenticated_user(user)
    if not isinstance(permission, str) or not permission:
        return False
    return permission in ROLE_PERMISSIONS[user.role]


def require_permission(user: AuthenticatedUser, permission: str) -> None:
    """Raise unless the role has the requested explicitly configured grant."""
    if not has_permission(user, permission):
        raise AuthorizationError("Permission denied.")


def get_authorized_cost_centre(user: AuthenticatedUser) -> str:
    """Resolve a manager's assigned cost-centre scope.

    Employee scope is per-user and Admin scope is organization-wide; neither
    can safely be represented by this single-cost-centre helper.
    """
    _require_authenticated_user(user)
    if user.role != "Manager":
        raise AuthorizationError("This identity does not have a single cost-centre scope.")
    require_permission(user, "expense:view_cost_centre")
    if not isinstance(user.cost_centre, str) or not user.cost_centre.strip():
        raise AuthorizationError("Authorized cost-centre scope is unavailable.")
    return user.cost_centre


def authorize_cost_centre(
    user: AuthenticatedUser, requested_cost_centre: str | None = None
) -> str:
    """Authorize a single-centre operation and return its safe filter value.

    Managers are restricted to their assigned centre. Admins may select a
    specific centre because they hold organization-wide access. Employees
    have user scope and cannot use this API to expand it to a whole centre.
    """
    _require_authenticated_user(user)
    if user.role == "Manager":
        authorized = get_authorized_cost_centre(user)
        if requested_cost_centre is not None and requested_cost_centre != authorized:
            raise AuthorizationError("Access to the requested cost centre is denied.")
        return authorized
    if user.role == "Admin":
        require_permission(user, "cost_centre:view_all")
        if not isinstance(requested_cost_centre, str) or not requested_cost_centre.strip():
            raise AuthorizationError("Select a cost centre for this single-centre operation.")
        return requested_cost_centre
    raise AuthorizationError("Employee access is limited to the authenticated user's data.")


def authorize_role(user: AuthenticatedUser, requested_role: str | None = None) -> str:
    """Return the database-authenticated role, rejecting a conflicting override."""
    _require_authenticated_user(user)
    authenticated_role = validate_role(user.role)
    if requested_role is not None and requested_role != authenticated_role:
        raise AuthorizationError("Access using the requested role is denied.")
    return authenticated_role


def resolve_authorized_scope(
    user: AuthenticatedUser,
    requested_cost_centre: str | None = None,
    *,
    requested_role: str | None = None,
    requested_user_id: str | None = None,
) -> dict[str, str]:
    """Return the role-derived data scope, rejecting attempted scope escalation."""
    _require_authenticated_user(user)
    role = authorize_role(user, requested_role)
    if not isinstance(user.user_id, str) or not user.user_id.strip():
        raise AuthorizationError("Authenticated user identity is unavailable.")

    if role == "Employee":
        require_permission(user, "expense:view_own")
        if requested_user_id is not None and requested_user_id != user.user_id:
            raise AuthorizationError("Access to another user's data is denied.")
        if requested_cost_centre is not None:
            raise AuthorizationError("Employee scope cannot be changed to a cost centre.")
        return {
            "user_id": user.user_id,
            "role": role,
            "scope_type": "user",
            "scope_user_id": user.user_id,
        }

    if role == "Manager":
        authorized = get_authorized_cost_centre(user)
        if requested_cost_centre is not None and requested_cost_centre != authorized:
            raise AuthorizationError("Access to the requested cost centre is denied.")
        return {
            "user_id": user.user_id,
            "role": role,
            "scope_type": "cost_centre",
            "cost_centre": authorized,
        }

    require_permission(user, "cost_centre:view_all")
    if requested_cost_centre is not None:
        raise AuthorizationError(
            "Organization scope cannot be replaced by a request cost-centre filter."
        )
    return {"user_id": user.user_id, "role": role, "scope_type": "organization"}


def get_authorized_scope(
    user: AuthenticatedUser,
    requested_cost_centre: str | None = None,
    *,
    requested_role: str | None = None,
    requested_user_id: str | None = None,
) -> dict[str, str]:
    """Return trusted identity plus user, cost-centre, or organization scope."""
    return resolve_authorized_scope(
        user,
        requested_cost_centre,
        requested_role=requested_role,
        requested_user_id=requested_user_id,
    )


def authorize_role_assignment(
    actor: AuthenticatedUser, new_role: str, target_user_id: str | None = None
) -> str:
    """Authorize assigning/changing a role; never performs a user mutation."""
    require_permission(actor, "user:manage")
    require_permission(actor, "role:assign")
    role = validate_role(new_role)
    if target_user_id is not None and (
        not isinstance(target_user_id, str) or not target_user_id.strip()
    ):
        raise AuthorizationError("Target user identity is invalid.")
    return role


def authorize_cost_centre_access_management(
    actor: AuthenticatedUser, target_user_id: str, cost_centre: str
) -> None:
    """Authorize changing a user's cost-centre access without mutating data."""
    require_permission(actor, "cost_centre:manage_access")
    if not isinstance(target_user_id, str) or not target_user_id.strip():
        raise AuthorizationError("Target user identity is invalid.")
    if not isinstance(cost_centre, str) or not cost_centre.strip():
        raise AuthorizationError("Cost-centre value is invalid.")


def authorize_expense_creation(
    user: AuthenticatedUser,
    requested_user_id: str | None = None,
    requested_cost_centre: str | None = None,
) -> dict[str, str]:
    """Authorize a future own-expense operation and return trusted fields only."""
    require_permission(user, "expense:create_own")
    if not isinstance(user.user_id, str) or not user.user_id.strip():
        raise AuthorizationError("Authenticated user identity is unavailable.")
    if requested_user_id is not None and requested_user_id != user.user_id:
        raise AuthorizationError("Users may create expenses only for themselves.")
    if not isinstance(user.cost_centre, str) or not user.cost_centre.strip():
        raise AuthorizationError("Authorized cost-centre scope is unavailable.")
    if requested_cost_centre is not None and requested_cost_centre != user.cost_centre:
        raise AuthorizationError("Expense cost-centre must match authenticated identity.")
    return {"user_id": user.user_id, "cost_centre": user.cost_centre}


def _require_authenticated_user(user: AuthenticatedUser) -> None:
    if not isinstance(user, AuthenticatedUser) or not user._is_trusted():
        raise AuthorizationError("Authentication is required.")
    try:
        validate_role(user.role)
    except ValueError:
        raise AuthorizationError("The authenticated role is invalid.") from None
