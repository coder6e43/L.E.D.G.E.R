"""Fail-closed role and cost-centre authorization helpers for LEDGER."""

from types import MappingProxyType
from typing import Mapping

from auth.authentication import AuthenticatedUser, VALID_ROLES

# Business permissions are intentionally unassigned until the product owners
# specify them. Unknown or unconfigured permissions are denied by default.
ROLE_PERMISSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {role: frozenset() for role in VALID_ROLES}
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
    """Resolve the sole authorized cost centre from authenticated identity."""
    _require_authenticated_user(user)
    if not isinstance(user.cost_centre, str) or not user.cost_centre.strip():
        raise AuthorizationError("Authorized cost-centre scope is unavailable.")
    return user.cost_centre


def authorize_cost_centre(
    user: AuthenticatedUser, requested_cost_centre: str | None = None
) -> str:
    """Return the authenticated user's scope, rejecting any different request."""
    authorized = get_authorized_cost_centre(user)
    if requested_cost_centre is not None and requested_cost_centre != authorized:
        raise AuthorizationError("Access to the requested cost centre is denied.")
    return authorized


def resolve_authorized_scope(
    user: AuthenticatedUser, requested_cost_centre: str | None = None
) -> dict[str, str]:
    """Build the trusted identity/scope mapping expected by integrations."""
    _require_authenticated_user(user)
    return {
        "user_id": user.user_id,
        "role": validate_role(user.role),
        "cost_centre": authorize_cost_centre(user, requested_cost_centre),
    }


def _require_authenticated_user(user: AuthenticatedUser) -> None:
    if not isinstance(user, AuthenticatedUser):
        raise AuthorizationError("Authentication is required.")
    validate_role(user.role)

