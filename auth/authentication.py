"""Database-backed credential verification for LEDGER."""

from __future__ import annotations

from dataclasses import dataclass, field

import bcrypt

from database.connection import get_connection

VALID_ROLES = frozenset({"Manager", "Employee", "Admin"})
GENERIC_AUTHENTICATION_ERROR = "Invalid email or password."
_AUTHENTICATED_USER_SEAL = object()


@dataclass(frozen=True, init=False)
class AuthenticatedUser:
    """Safe authenticated identity; never contains a password or password hash."""

    user_id: str
    name: str
    email: str
    role: str
    cost_centre: str
    _seal: object = field(repr=False, compare=False)

    def __init__(self, *_args, **_kwargs) -> None:
        raise TypeError("AuthenticatedUser instances are created by authentication only.")

    @classmethod
    def _from_database(cls, row) -> "AuthenticatedUser":
        """Mint an identity from a verified database record."""
        user = object.__new__(cls)
        object.__setattr__(user, "user_id", row["user_id"])
        object.__setattr__(user, "name", row["name"])
        object.__setattr__(user, "email", row["email"])
        object.__setattr__(user, "role", row["role"])
        object.__setattr__(user, "cost_centre", row["cost_centre"])
        object.__setattr__(user, "_seal", _AUTHENTICATED_USER_SEAL)
        return user

    def _is_trusted(self) -> bool:
        """Whether this identity was minted by the authentication module."""
        return getattr(self, "_seal", None) is _AUTHENTICATED_USER_SEAL

    def to_dict(self) -> dict[str, str]:
        """Return the public identity fields used by application integrations."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "cost_centre": self.cost_centre,
        }


# Computing this once lets unknown accounts and malformed demo hashes take a
# password-hash verification path too, without embedding a usable credential.
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(
    b"LEDGER dummy verification only", bcrypt.gensalt()
)


def authenticate_user(email: str, password: str) -> AuthenticatedUser | None:
    """Return a trusted user for valid credentials, or ``None`` on any failure.

    The SQL is parameterized and retrieves only the fields needed for login.
    Stored hashes that are malformed (including sample placeholders) fail
    closed. Credential values are never logged or included in the result.
    """
    if not isinstance(email, str) or not isinstance(password, str):
        return None

    normalized_email = email.strip().casefold()
    if not normalized_email or not password:
        return None

    try:
        password_bytes = password.encode("utf-8")
    except UnicodeError:
        return None
    if len(password_bytes) > 72:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """SELECT user_id, name, email, password_hash, role, cost_centre
               FROM users WHERE lower(email) = lower(?)""",
            (normalized_email,),
        ).fetchone()

    if row is None:
        _verify_against_dummy(password_bytes)
        return None

    try:
        stored_hash = row["password_hash"]
        if not isinstance(stored_hash, (str, bytes)):
            raise ValueError("Invalid stored password hash")
        hash_bytes = stored_hash.encode("ascii") if isinstance(stored_hash, str) else stored_hash
        password_matches = bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError, UnicodeError):
        _verify_against_dummy(password_bytes)
        return None

    role = row["role"]
    if not password_matches or role not in VALID_ROLES:
        return None

    return AuthenticatedUser._from_database(row)


def load_session_user(user_id: str) -> AuthenticatedUser | None:
    """Reload a user's current safe identity for a verified session cookie.

    The caller must obtain ``user_id`` from the backend-signed session. Role
    and cost-centre values are always refreshed from the database rather than
    accepted from cookie contents.
    """
    if not isinstance(user_id, str) or not user_id.strip():
        return None
    with get_connection() as conn:
        row = conn.execute(
            """SELECT user_id, name, email, role, cost_centre
               FROM users WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
    if row is None or row["role"] not in VALID_ROLES:
        return None
    return AuthenticatedUser._from_database(row)


def _verify_against_dummy(password_bytes: bytes) -> None:
    """Spend bcrypt verification work without exposing account existence."""
    bcrypt.checkpw(password_bytes, _DUMMY_PASSWORD_HASH)

