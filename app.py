"""LEDGER backend integration boundary and FastAPI application.

Provides:
- FastAPI application with Query Compiler router
- Authenticated session management (login, logout, get_current_user)
- End-to-end query execution with Auth -> RBAC -> Query Compiler -> Calculation -> Audit
"""

from __future__ import annotations

import json
import math
import re
import time
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from audit.api import router as audit_router
from audit.logger import DEFAULT_DB, log_query
from auth.authentication import AuthenticatedUser, authenticate_user
from auth.rbac import AuthorizationError, get_authorized_scope, has_permission
from auth.session import (
    get_current_user,
    logout as clear_session,
    set_authenticated_user,
)
from calculation.engine import SUPPORTED_INTENTS, run_calculation
from database.ingestion import ALLOWED_CATEGORIES, ALLOWED_CURRENCIES
from query.api import get_trusted_scope, router as query_router
from query.compiler import compile_query
from query.schema import AuthorizationScope, ScopeType, Status

app = FastAPI(title="LEDGER API")
app.include_router(query_router)
app.include_router(audit_router)


# -----------------------------------------------------------------------------
# Session / Context Helpers
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# End-to-End Query Execution & Audit Integration
# -----------------------------------------------------------------------------


def run_authenticated_query(
    query: Mapping[str, Any] | str,
    *,
    db_path: Path = DEFAULT_DB,
    current_date: date | None = None,
) -> dict[str, Any]:
    """Execute and audit a financial query within the authenticated session context.

    Expected flow:
        User -> Authentication -> RBAC -> Query Compiler -> Calculation -> Audit -> Response

    Accepts either:
    1. A natural language prompt string (or mapping with 'prompt' key), which
       is compiled into a structured query via Query Compiler and executed.
    2. A structured query mapping (for backwards compatibility / direct execution).
    """
    user = get_current_user()
    if user is None:
        return _failure("ACCESS_DENIED", "Authentication is required.")

    if not has_permission(user, "query:ask"):
        safe_prompt = _get_safe_prompt(query)
        scope_str = getattr(user, "cost_centre", None) or "UNKNOWN"
        try:
            log_query(
                user_id=user.user_id,
                scope=scope_str,
                raw_prompt=safe_prompt,
                status="ACCESS_DENIED",
                parsed_query={"authenticated_role": user.role},
                applied_filters={"cost_centre": scope_str},
                source_row_ids=None,
                numeric_result=None,
                db_path=db_path,
            )
        except Exception:
            pass
        return _failure("ACCESS_DENIED", "You are not authorized to ask financial queries.")

    try:
        authorization = get_authorized_scope(user)
    except AuthorizationError as exc:
        safe_prompt = _get_safe_prompt(query)
        scope_str = getattr(user, "cost_centre", None) or "UNKNOWN"
        try:
            log_query(
                user_id=user.user_id,
                scope=scope_str,
                raw_prompt=safe_prompt,
                status="ACCESS_DENIED",
                parsed_query={"error": str(exc), "authenticated_role": user.role},
                applied_filters={"cost_centre": scope_str},
                source_row_ids=None,
                numeric_result=None,
                db_path=db_path,
            )
        except Exception:
            pass
        return _failure("ACCESS_DENIED", str(exc))

    if authorization.get("scope_type") != "cost_centre":
        safe_prompt = _get_safe_prompt(query)
        scope_str = (
            getattr(user, "cost_centre", None)
            or authorization.get("cost_centre")
            or authorization.get("scope_type", "UNKNOWN")
        )
        try:
            log_query(
                user_id=user.user_id,
                scope=scope_str,
                raw_prompt=safe_prompt,
                status="ACCESS_DENIED",
                parsed_query={
                    "scope_type": authorization.get("scope_type"),
                    "authenticated_role": user.role,
                },
                applied_filters={"cost_centre": scope_str},
                source_row_ids=None,
                numeric_result=None,
                db_path=db_path,
            )
        except Exception:
            pass
        return _failure(
            "SCOPE_UNSUPPORTED",
            "The calculation integration cannot safely execute this authorization scope yet.",
        )

    scope = authorization["cost_centre"]

    # Determine whether input is natural language prompt or pre-structured
    is_prompt_input = isinstance(query, str) or (
        isinstance(query, Mapping) and "prompt" in query
    )

    if is_prompt_input:
        raw_prompt_text = query if isinstance(query, str) else str(query["prompt"])
        safe_prompt = _sanitize_prompt(raw_prompt_text)

        auth_scope = AuthorizationScope(
            user_id=user.user_id,
            role=user.role,
            scope_type=ScopeType.cost_centre,
            cost_centre=scope,
        )

        start_time = time.perf_counter()
        compiler_resp = compile_query(
            prompt=raw_prompt_text,
            scope=auth_scope,
            current_date=current_date,
        )

        if compiler_resp.status == Status.CLARIFY:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            try:
                qid = log_query(
                    user_id=user.user_id,
                    scope=scope,
                    raw_prompt=safe_prompt,
                    status="CLARIFY",
                    parsed_query={
                        "message": compiler_resp.message,
                        "authenticated_role": user.role,
                    },
                    applied_filters={"cost_centre": scope},
                    source_row_ids=None,
                    numeric_result=None,
                    latency_ms=latency_ms,
                    db_path=db_path,
                )
            except Exception:
                return _failure("AUDIT_ERROR", "The query could not be completed.")
            return {
                "status": "CLARIFY",
                "message": compiler_resp.message,
                "result": None,
                "currency": None,
                "source_rows": [],
                "query_id": qid,
            }

        if compiler_resp.status == Status.REFUSED:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            try:
                qid = log_query(
                    user_id=user.user_id,
                    scope=scope,
                    raw_prompt=safe_prompt,
                    status="REFUSED",
                    parsed_query={
                        "message": compiler_resp.message,
                        "authenticated_role": user.role,
                    },
                    applied_filters={"cost_centre": scope},
                    source_row_ids=None,
                    numeric_result=None,
                    latency_ms=latency_ms,
                    db_path=db_path,
                )
            except Exception:
                return _failure("AUDIT_ERROR", "The query could not be completed.")
            return {
                "status": "REFUSED",
                "message": compiler_resp.message,
                "result": None,
                "currency": None,
                "source_rows": [],
                "query_id": qid,
            }

        compiled_q = compiler_resp.query
        calc_query = {
            "intent": compiled_q.intent.value,
            "category": compiled_q.category,
            "date_range_start": (
                compiled_q.date_range_start.isoformat()
                if compiled_q.date_range_start
                else None
            ),
            "date_range_end": (
                compiled_q.date_range_end.isoformat()
                if compiled_q.date_range_end
                else None
            ),
            "limit": compiled_q.limit,
            "currency": compiled_q.currency,
        }
        intent = compiled_q.intent.value
        parsed_audit_query = calc_query
    else:
        calc_query = dict(query) if isinstance(query, Mapping) else {}
        intent = calc_query.get("intent")
        if intent == "expense_count":
            intent = "count_expenses"
            calc_query["intent"] = "count_expenses"
        safe_query = _safe_query_for_audit(calc_query)
        safe_prompt = json.dumps(safe_query, sort_keys=True)
        parsed_audit_query = safe_query

    required_permission = (
        "budget:view_cost_centre"
        if isinstance(intent, str) and intent in {"remaining_budget", "burn_rate"}
        else "expense:view_cost_centre"
    )
    if not has_permission(user, required_permission):
        try:
            log_query(
                user_id=user.user_id,
                scope=scope,
                raw_prompt=safe_prompt,
                status="ACCESS_DENIED",
                parsed_query={
                    "query": parsed_audit_query,
                    "authenticated_role": user.role,
                },
                applied_filters={"cost_centre": scope},
                source_row_ids=None,
                numeric_result=None,
                db_path=db_path,
            )
        except Exception:
            pass
        return _failure("ACCESS_DENIED", "You are not authorized for this query operation.")

    start_time = time.perf_counter()
    result = run_calculation(calc_query, authorized_cost_centre=scope)
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    safe_query = _safe_query_for_audit(calc_query)
    result_status = result.get("status")

    if result_status == "SUCCESS":
        audit_status = "SUCCESS"
        source_rows = result.get("source_rows")
        if source_rows is None:
            source_rows = []
        numeric_result = result.get("result")
        if (
            isinstance(numeric_result, bool)
            or not isinstance(numeric_result, (int, float))
            or not math.isfinite(numeric_result)
        ):
            numeric_result = None
    else:
        audit_status = (
            "ACCESS_DENIED"
            if result_status in {"ACCESS_DENIED", "MISSING_AUTHORIZED_SCOPE", "USER_SCOPE_CONFLICT"}
            else "REFUSED"
        )
        source_rows = None
        numeric_result = None

    applied_filters = {
        "cost_centre": scope,
        **{
            k: v
            for k, v in safe_query.items()
            if k != "intent" and v is not None and v != "invalid"
        },
    }

    try:
        query_id = log_query(
            user_id=user.user_id,
            scope=scope,
            raw_prompt=safe_prompt,
            status=audit_status,
            parsed_query={"query": safe_query, "authenticated_role": user.role},
            applied_filters=applied_filters,
            source_row_ids=source_rows,
            numeric_result=numeric_result,
            latency_ms=latency_ms,
            db_path=db_path,
        )
    except Exception:
        # Do not return calculated financial data if its audit record could not
        # be written. The response stays generic and contains no partial result.
        return _failure("AUDIT_ERROR", "The query could not be completed.")

    result["query_id"] = query_id
    return result


def _sanitize_prompt(prompt: str) -> str:
    """Redact passwords and credentials from natural language query prompts."""
    if not isinstance(prompt, str):
        return ""
    # Redact key=value or key: value or 'key is value' patterns
    sanitized = re.sub(
        r"(?i)\b(password|secret|token|api_key|password_hash|pwd)\s*(?:=|:|\bis\b)\s*([^\s,;]+)",
        r"\1: [REDACTED]",
        prompt,
    )
    return sanitized


def _get_safe_prompt(query: Any) -> str:
    """Produce a safe raw prompt representation without credentials."""
    if isinstance(query, str):
        return _sanitize_prompt(query)
    if isinstance(query, Mapping):
        if "prompt" in query and isinstance(query["prompt"], str):
            return _sanitize_prompt(query["prompt"])
        safe = _safe_query_for_audit(query)
        return json.dumps(safe, sort_keys=True)
    return ""


def _safe_query_for_audit(query: Any) -> dict[str, Any]:
    """Keep only recognized, non-sensitive structured fields in audit data."""
    if not isinstance(query, Mapping):
        return {}

    safe: dict[str, Any] = {}
    intent = query.get("intent")
    if intent == "expense_count":
        intent = "count_expenses"
    safe["intent"] = (
        intent
        if isinstance(intent, str) and (intent in SUPPORTED_INTENTS or intent in {"burn_rate", "count_expenses"})
        else "unsupported"
    )

    category = query.get("category")
    if category is not None:
        safe["category"] = (
            category
            if isinstance(category, str) and category in ALLOWED_CATEGORIES
            else "invalid"
        )

    for key in ("date_start", "date_end", "date_range_start", "date_range_end"):
        value = query.get(key)
        if value is not None:
            if isinstance(value, date):
                safe[key] = value.isoformat()
            else:
                safe[key] = _valid_iso_date(value)

    currency = query.get("currency")
    if currency is not None:
        safe["currency"] = (
            currency
            if isinstance(currency, str) and currency in ALLOWED_CURRENCIES
            else "invalid"
        )

    for top_key in ("top_n", "limit"):
        top_val = query.get(top_key)
        if top_val is not None:
            safe[top_key] = (
                top_val
                if isinstance(top_val, int)
                and not isinstance(top_val, bool)
                and top_val > 0
                else "invalid"
            )

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


# -----------------------------------------------------------------------------
# End-to-End Execution Endpoint
# -----------------------------------------------------------------------------


class ExecuteQueryRequest(BaseModel):
    """Client input for end-to-end execution. Authorization fields forbidden."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    current_date: Optional[date] = None


@app.post("/query/execute")
def execute_query_endpoint(
    request: ExecuteQueryRequest,
    scope: AuthorizationScope = Depends(get_trusted_scope),
) -> dict[str, Any]:
    """Execute a financial query end-to-end and record audit trail."""
    result = run_authenticated_query(
        request.prompt,
        current_date=request.current_date,
    )
    if result.get("status") == "ACCESS_DENIED":
        raise HTTPException(status_code=403, detail=result.get("error", "Access denied."))
    return result
