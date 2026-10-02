"""Small backend integration boundary for the current LEDGER modules.

The query compiler and frontend are not implemented yet. This module accepts
their future structured-query output and ensures execution uses the identity
and cost-centre from the current authenticated context.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from audit.logger import log_query
from auth.authentication import AuthenticatedUser, authenticate_user
from auth.rbac import get_authorized_cost_centre
from auth.session import (
    get_current_user,
    logout as clear_session,
    set_authenticated_user,
)
from calculation.engine import SUPPORTED_INTENTS, run_calculation
from database.ingestion import ALLOWED_CATEGORIES, ALLOWED_CURRENCIES

_AUDIT_QUERY_FIELDS = ("intent", "category", "date_start", "date_end", "currency", "top_n")


def login_user(email: str, password: str) -> AuthenticatedUser | None:
    """Authenticate and set the current context; return ``None`` on failure."""
    clear_session()
    user = authenticate_user(email, password)
    if user is not None:
        set_authenticated_user(user)
    return user


def logout_user() -> None:
    """Clear the authenticated identity from the current execution context."""
    clear_session()


def run_authenticated_query(query: Mapping[str, Any]) -> dict[str, Any]:
    """Run and audit one structured query using the authenticated user's scope.

    The frontend or query compiler cannot provide an authorized scope through
    this interface. Only the current authenticated identity supplies it.
    """
    user = get_current_user()
    if user is None:
        return _failure("ACCESS_DENIED", "Authentication is required.")

    scope = get_authorized_cost_centre(user)
    result = run_calculation(query, authorized_cost_centre=scope)
    safe_query = _safe_query_for_audit(query)
    result_status = result.get("status")
    audit_status = "SUCCESS" if result_status == "SUCCESS" else (
        "ACCESS_DENIED" if result_status in {"ACCESS_DENIED", "MISSING_AUTHORIZED_SCOPE"}
        else "REFUSED"
    )
    numeric_result = result.get("result")
    if isinstance(numeric_result, bool) or not isinstance(numeric_result, (int, float)):
        numeric_result = None
    elif not math.isfinite(numeric_result):
        numeric_result = None

    try:
        log_query(
            user_id=user.user_id,
            scope=scope,
            # Store only the validated structured fields, never raw user text.
            raw_prompt=json.dumps(safe_query, sort_keys=True),
            status=audit_status,
            parsed_query={"query": safe_query, "authenticated_role": user.role},
            applied_filters={
                "cost_centre": scope,
                **{key: value for key, value in safe_query.items() if key != "intent"},
            },
            source_row_ids=result.get("source_rows") if audit_status == "SUCCESS" else None,
            numeric_result=numeric_result,
        )
    except Exception:
        # Do not return calculated financial data if its audit record could not
        # be written. The response stays generic and contains no partial result.
        return _failure("AUDIT_ERROR", "The query could not be completed.")

    return result


def _safe_query_for_audit(query: Any) -> dict[str, Any]:
    """Keep only recognized, non-sensitive structured fields in audit data."""
    if not isinstance(query, Mapping):
        return {}

    safe: dict[str, Any] = {}
    intent = query.get("intent")
    safe["intent"] = intent if isinstance(intent, str) and intent in SUPPORTED_INTENTS else "unsupported"

    category = query.get("category")
    if category is not None:
        safe["category"] = (
            category if isinstance(category, str) and category in ALLOWED_CATEGORIES else "invalid"
        )

    for key in ("date_start", "date_end"):
        value = query.get(key)
        if value is not None:
            safe[key] = _valid_iso_date(value)

    currency = query.get("currency")
    if currency is not None:
        safe["currency"] = (
            currency if isinstance(currency, str) and currency in ALLOWED_CURRENCIES else "invalid"
        )

    top_n = query.get("top_n")
    if top_n is not None:
        safe["top_n"] = top_n if isinstance(top_n, int) and not isinstance(top_n, bool) and top_n > 0 else "invalid"

    return safe


def _valid_iso_date(value: Any) -> str:
    if not isinstance(value, str):
        return "invalid"
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return "invalid"
    return value if parsed.strftime("%Y-%m-%d") == value else "invalid"


def _failure(status: str, message: str) -> dict[str, Any]:
    return {
        "status": status,
        "result": None,
        "currency": None,
        "source_rows": [],
        "error": message,
    }
