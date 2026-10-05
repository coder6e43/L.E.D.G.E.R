"""Context-local authenticated identity helpers for a single request/task."""

from __future__ import annotations

from contextvars import ContextVar

from auth.authentication import AuthenticatedUser, VALID_ROLES

_current_user: ContextVar[AuthenticatedUser | None] = ContextVar(
    "ledger_current_user", default=None
)


def set_authenticated_user(user: AuthenticatedUser) -> None:
    """Set the server-authenticated identity for the current execution context."""
    if (
        not isinstance(user, AuthenticatedUser)
        or not user._is_trusted()
        or user.role not in VALID_ROLES
    ):
        raise TypeError("Only a valid AuthenticatedUser may be placed in session state.")
    _current_user.set(user)


def get_current_user() -> AuthenticatedUser | None:
    """Return the authenticated identity for this execution context, if any."""
    return _current_user.get()


def is_authenticated() -> bool:
    """Whether the current execution context has an authenticated identity."""
    return get_current_user() is not None


def logout() -> None:
    """Clear authenticated identity from the current execution context."""
    _current_user.set(None)

