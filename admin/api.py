"""Admin-only user directory and account management endpoints."""

from __future__ import annotations

import re
import uuid
from typing import Literal

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from audit.logger import log_query
from auth.rbac import (
    AuthorizationError,
    authorize_cost_centre_access_management,
    authorize_role_assignment,
    has_permission,
)
from auth.session import get_current_user
from database.connection import get_connection

router = APIRouter(prefix="/admin", tags=["Admin"])
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_VALID_ROLES = {"Employee", "Manager", "Admin"}


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=72)
    role: Literal["Employee", "Manager", "Admin"]
    cost_centre: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes.")
        return value

    @field_validator("cost_centre")
    @classmethod
    def clean_cost_centre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Cost centre is required.")
        return value


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["Employee", "Manager", "Admin"]


class CostCentreUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cost_centre: str = Field(min_length=1, max_length=64)

    @field_validator("cost_centre")
    @classmethod
    def clean_cost_centre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Cost centre is required.")
        return value


def require_admin(permission: str = "user:manage"):
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Administrator permission required.")
    return user


def _safe_user(row) -> dict[str, str]:
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "cost_centre": row["cost_centre"],
    }


def _supported_cost_centres(conn) -> list[str]:
    rows = conn.execute(
        """SELECT cost_centre FROM users
           UNION SELECT cost_centre FROM expenses
           UNION SELECT cost_centre FROM budgets
           ORDER BY cost_centre"""
    ).fetchall()
    return [row["cost_centre"] for row in rows if row["cost_centre"]]


def _audit_admin_action(actor, action: str, target_user_id: str, details: dict) -> None:
    scope = actor.cost_centre if actor.role != "Admin" else "organization"
    log_query(
        user_id=actor.user_id,
        scope=scope,
        raw_prompt=action,
        status="SUCCESS",
        parsed_query={"action": action, "target_user_id": target_user_id, **details},
        applied_filters={"actor_role": actor.role, "scope_value": scope},
        source_row_ids=[],
    )


@router.get("/summary")
def admin_summary(user=Depends(require_admin)) -> dict:
    with get_connection() as conn:
        users_by_role = conn.execute(
            "SELECT role, COUNT(*) AS count FROM users GROUP BY role ORDER BY role"
        ).fetchall()
        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        expense_count = conn.execute("SELECT COUNT(*) AS count FROM expenses").fetchone()["count"]
        totals = conn.execute(
            "SELECT currency, SUM(amount) AS amount FROM expenses GROUP BY currency ORDER BY currency"
        ).fetchall()
        cost_centres = _supported_cost_centres(conn)
    return {
        "user_count": user_count,
        "users_by_role": [{"role": row["role"], "count": row["count"]} for row in users_by_role],
        "expense_count": expense_count,
        "spend_by_currency": [{"currency": row["currency"], "amount": row["amount"] or 0} for row in totals],
        "cost_centres": cost_centres,
    }


@router.get("/options")
def admin_options(user=Depends(require_admin)) -> dict[str, list[str]]:
    with get_connection() as conn:
        return {"roles": sorted(_VALID_ROLES), "cost_centres": _supported_cost_centres(conn)}


@router.get("/users")
def list_users(
    search: str = Query(default="", max_length=100),
    role: str | None = Query(default=None),
    cost_centre: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=200, ge=1, le=500),
    user=Depends(require_admin),
) -> list[dict[str, str]]:
    conditions: list[str] = []
    params: list[object] = []
    if search.strip():
        term = f"%{search.strip()}%"
        conditions.append("(user_id LIKE ? OR name LIKE ? OR email LIKE ?)")
        params.extend((term, term, term))
    if role is not None:
        if role not in _VALID_ROLES:
            raise HTTPException(status_code=422, detail="Invalid role filter.")
        conditions.append("role = ?")
        params.append(role)
    if cost_centre is not None:
        conditions.append("cost_centre = ?")
        params.append(cost_centre)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT user_id, name, email, role, cost_centre FROM users {where} ORDER BY name, user_id LIMIT ?",
            (*params, limit),
        ).fetchall()
    return [_safe_user(row) for row in rows]


@router.post("/users", status_code=201)
def create_user(payload: CreateUserRequest, user=Depends(require_admin)) -> dict[str, str]:
    user_id = f"U{uuid.uuid4().hex[:12].upper()}"
    password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    try:
        with get_connection() as conn:
            if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (payload.email,)).fetchone():
                raise HTTPException(status_code=409, detail="A user with that email already exists.")
            if payload.cost_centre not in _supported_cost_centres(conn):
                raise HTTPException(status_code=422, detail="Select a supported cost centre.")
            conn.execute(
                "INSERT INTO users (user_id, name, email, password_hash, role, cost_centre) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, payload.name, payload.email, password_hash, payload.role, payload.cost_centre),
            )
            row = conn.execute(
                "SELECT user_id, name, email, role, cost_centre FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
    except HTTPException:
        raise
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="A user with that email already exists.") from None
        raise
    safe = _safe_user(row)
    _audit_admin_action(user, "admin.create_user", user_id, {"role": payload.role, "cost_centre": payload.cost_centre})
    return safe


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: str, payload: RoleUpdateRequest, user=Depends(require_admin)) -> dict[str, str]:
    try:
        role = authorize_role_assignment(user, payload.role, user_id)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Role assignment is not authorized.") from exc
    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="User not found.")
        conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        row = conn.execute("SELECT user_id, name, email, role, cost_centre FROM users WHERE user_id = ?", (user_id,)).fetchone()
    safe = _safe_user(row)
    _audit_admin_action(user, "admin.update_role", user_id, {"role": role})
    return safe


@router.patch("/users/{user_id}/cost-centre")
def update_user_cost_centre(user_id: str, payload: CostCentreUpdateRequest, user=Depends(require_admin)) -> dict[str, str]:
    try:
        authorize_cost_centre_access_management(user, user_id, payload.cost_centre)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Cost-centre assignment is not authorized.") from exc
    with get_connection() as conn:
        if conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="User not found.")
        if payload.cost_centre not in _supported_cost_centres(conn):
            raise HTTPException(status_code=422, detail="Select a supported cost centre.")
        conn.execute("UPDATE users SET cost_centre = ? WHERE user_id = ?", (payload.cost_centre, user_id))
        row = conn.execute("SELECT user_id, name, email, role, cost_centre FROM users WHERE user_id = ?", (user_id,)).fetchone()
    safe = _safe_user(row)
    _audit_admin_action(user, "admin.update_cost_centre", user_id, {"cost_centre": payload.cost_centre})
    return safe
