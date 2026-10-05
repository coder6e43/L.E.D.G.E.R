"""Create expenses for the authenticated user using trusted RBAC fields."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from audit.logger import log_query
from auth.rbac import AuthorizationError, authorize_expense_creation, get_authorized_scope
from auth.session import get_current_user
from database.connection import get_connection
from database.ingestion import ALLOWED_CATEGORIES, ALLOWED_CURRENCIES

router = APIRouter(prefix="/expenses", tags=["Expenses"])


class ExpenseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    amount: float = Field(ge=0, allow_inf_nan=False)
    currency: str
    date: date
    description: str = Field(default="", max_length=500)

    @field_validator("category")
    @classmethod
    def valid_category(cls, value: str) -> str:
        if value not in ALLOWED_CATEGORIES:
            raise ValueError("Select a supported expense category.")
        return value

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        if value not in ALLOWED_CURRENCIES:
            raise ValueError("Select a supported currency.")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return value.strip()


@router.post("", status_code=201)
def create_expense(payload: ExpenseCreateRequest) -> dict:
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        trusted_fields = authorize_expense_creation(user)
        scope = get_authorized_scope(user)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Expense creation is not authorized.") from exc

    expense_id = f"EXP-{uuid.uuid4().hex[:12].upper()}"
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO expenses
               (expense_id, user_id, cost_centre, category, amount, currency, date, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                expense_id,
                trusted_fields["user_id"],
                trusted_fields["cost_centre"],
                payload.category,
                payload.amount,
                payload.currency,
                payload.date.isoformat(),
                payload.description,
            ),
        )

    try:
        log_query(
            user_id=user.user_id,
            scope=scope["scope_value"],
            raw_prompt="expense:create_own",
            status="SUCCESS",
            parsed_query={
                "action": "expense.create",
                "expense_id": expense_id,
                "category": payload.category,
                "amount": payload.amount,
                "currency": payload.currency,
                "date": payload.date.isoformat(),
            },
            applied_filters={
                "scope_type": scope["scope_type"],
                "scope_value": scope["scope_value"],
                "user_id": user.user_id,
            },
            source_row_ids=[expense_id],
            numeric_result=payload.amount,
        )
    except Exception as exc:
        # Compensate if the configured audit store is unavailable; do not
        # report a successful write that lacks its required action record.
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM expenses WHERE expense_id = ? AND user_id = ?",
                (expense_id, user.user_id),
            )
        raise HTTPException(status_code=503, detail="The expense could not be recorded safely.") from exc

    return {
        "expense_id": expense_id,
        "user_id": user.user_id,
        "cost_centre": trusted_fields["cost_centre"],
        "category": payload.category,
        "amount": payload.amount,
        "currency": payload.currency,
        "date": payload.date.isoformat(),
        "description": payload.description,
    }
