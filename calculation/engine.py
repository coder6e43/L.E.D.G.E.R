"""
calculation/engine.py

The Deterministic Calculation Engine for L.E.D.G.E.R.

Responsibility (per INTEGRATION_CONTRACT.md, section 6):

    authorized query -> Database -> Deterministic Calculation -> Audit/Frontend

This module ONLY does: DATABASE -> FILTER -> FORMULA -> RESULT.
It never performs financial arithmetic itself -- every number in a result
comes from calculation/formulas.py. It never authenticates or authorizes a
user -- it only accepts an already-authorized SCOPE as a trusted input (see
AUTHORIZED SCOPE below) and applies it.

--------------------------------------------------------------------------
COMPATIBILITY NOTE (this module does not import auth/)
--------------------------------------------------------------------------
This module does NOT import from the `auth` package (auth/rbac.py). It
exposes one plain entry point:

    run_calculation(query: Mapping[str, Any], authorized_scope: Mapping[str, Any]) -> dict

`query` is produced by the Query Compiler (query/compiler.py,
query/schema.py), which this module also does not import from -- it only
reads plain fields off the `query` mapping it's handed. `authorized_scope`
is the dict returned by auth.get_authorized_scope() (on
origin/feature/auth-rbac) -- this module does not call that function
itself, it only consumes whatever dict the caller passes in. The engine
does not decide who is authorized for what; Auth/RBAC already made that
decision, and the engine's only job is to apply the scope it is handed.

--------------------------------------------------------------------------
AUTHORIZED SCOPE -- auth/rbac.py's ACTUAL return shapes
--------------------------------------------------------------------------
`authorized_scope` is expected to be exactly one of the three shapes
auth.get_authorized_scope() returns (field names match auth/rbac.py, not a
generic "scope_value"):

    Employee:
        {"user_id": ..., "role": "Employee",
         "scope_type": "user", "scope_user_id": "<id>"}

    Manager:
        {"user_id": ..., "role": "Manager",
         "scope_type": "cost_centre", "cost_centre": "<cc>"}

    Admin:
        {"user_id": ..., "role": "Admin",
         "scope_type": "organization"}

This module reads only "scope_type" plus the one field each scope_type
requires ("scope_user_id" for user, "cost_centre" for cost_centre, nothing
extra for organization). The "user_id" and "role" fields are ignored --
the engine does not re-derive or second-guess the authorization decision
from them; `scope_type` plus its one required field is the complete,
already-authorized instruction for how to filter the database:

    scope_type == "user"         -> expenses WHERE user_id = scope_user_id
    scope_type == "cost_centre"  -> expenses WHERE cost_centre = cost_centre
    scope_type == "organization" -> expenses: no additional restriction
                                     (the whole organization's expenses are
                                     in scope; NOT a fake cost_centre "ALL")

Budgets are a narrower case: database/models.py's `budgets` table is
cost-centre based only (no user or organization dimension). See BUDGET
SCOPE below for how each scope_type is handled for remaining_budget/
burn_rate.

run_calculation() fails closed on anything that doesn't match one of the
three shapes above -- see SCOPE VALIDATION below.

--------------------------------------------------------------------------
STRUCTURED QUERY -- LATEST QUERY COMPILER CONTRACT
--------------------------------------------------------------------------
The Query Compiler's query object contains:

    intent              (str, required)      -- see SUPPORTED_INTENTS below
    user_scope           (str, optional)     -- see QUERY SCOPE SECURITY
                                                 below; NEVER used to filter
                                                 the database
    category              (str, optional)
    date_range_start      (date, optional)   -- python datetime.date (or an
                                                 already-formatted
                                                 'YYYY-MM-DD' string)
    date_range_end         (date, optional)  -- same as above
    limit                   (int, optional)  -- used only by top_transactions
    currency                 (str, optional) -- defaults to "INR" per the
                                                 compiler schema; filters
                                                 expenses, never converts

This supersedes the older field names this engine previously used
(date_start/date_end/top_n/expense_ids); those are no longer read anywhere
in this file.

--------------------------------------------------------------------------
SUPPORTED INTENTS
--------------------------------------------------------------------------
The Query Compiler uses exactly these six intent names:

    sum_expenses        -> calculate_total_expenses()
    category_breakdown  -> calculate_category_spending()
    top_transactions     -> calculate_top_transactions()
    count_expenses        -> calculate_expense_count()
    remaining_budget       -> calculate_remaining_budget()
    source_lookup            -> direct filtered lookup of matching expense
                                 records (no formula math involved; pure
                                 evidence retrieval) -- this intent takes no
                                 expense_ids list (the compiler schema has
                                 none); it uses the same filters as every
                                 other intent (category, date_range_start/
                                 end, currency).

burn_rate (-> calculate_burn_rate()) is kept as an additional, non-compiler
engine capability: it is not one of the six names the compiler emits, but
nothing stops a caller that already knows this engine's extra capability
from using it, and it does not interfere with the six compiler intents.
No other intents/financial calculations are supported.

--------------------------------------------------------------------------
RESULT CONTRACT
--------------------------------------------------------------------------
INTEGRATION_CONTRACT.md section 4 defines the core output shape:

    {"result": ..., "currency": "INR", "source_rows": [...]}

Every result from run_calculation() keeps these three keys. Additional
metadata keys (status, formula, filters, row_count, budget_id, ...) are
appended without removing or renaming the core three, so contract-compatible
callers that only read result/currency/source_rows keep working unchanged.
`filters["scope"]` now reports the resolved, trusted scope dict that was
actually applied (see _build_filters), rather than a "cost_centre" key that
wouldn't make sense for user/organization scope.

CURRENCY FIELD: this engine performs NO currency conversion (per the schema
and ingestion contract, there is no exchange-rate field anywhere). If the
caller filters by an explicit "currency", the expense rows are filtered by
it first (as a real, parameterized SQL condition -- never merely echoed
back), then validated, then a formula runs. If no filter is given, the
matching expense rows are validated BEFORE any formula call: if they span
more than one currency, summing/ranking them would silently produce a
misleading number, so the engine returns MIXED_CURRENCY and never calls
calculate_total_expenses() / calculate_category_spending() /
calculate_top_transactions() / calculate_burn_rate() over that mixed set.
This validate-before-calculate ordering applies to every monetary intent
(sum_expenses, category_breakdown, remaining_budget, burn_rate), to
top_transactions (ranking mixed-currency amounts by raw value is an equally
misleading combination), and to source_lookup (returning mixed-currency
records while labeling them with one currency would be misleading).
count_expenses is a row count, not a monetary value, so no currency check
applies to it. If no currency filter is given and every matching row shares
one currency, that currency is used. If there are no matching rows and no
filter, the currency is reported as None (unknown, not guessed).

BUDGET CURRENCY: the budgets table has NO currency column (budget_id,
cost_centre, category, amount, period_start, period_end), and this file
does not add one or invent budget-currency semantics. For remaining_budget
and burn_rate, the top-level "currency" field describes the expense side
only (the side that actually has currency data); engine.py never assumes
the budget amount shares that currency. Both intents also return an
explicit "budget_currency": None, so a caller can never mistake "currency"
for a verified property of the budget amount.

FAILURE SHAPE: INTEGRATION_CONTRACT.md does not define a failure shape (only
a success example). Failures use the same three core keys, with
result=None, source_rows=[], plus "status" and "error" describing why:

    {"status": "BUDGET_NOT_FOUND", "result": None, "currency": None,
     "source_rows": [], "error": "..."}

--------------------------------------------------------------------------
SCOPE VALIDATION (fail closed)
--------------------------------------------------------------------------
run_calculation() validates `authorized_scope` before doing anything else:

    missing / not a mapping / empty        -> MISSING_AUTHORIZED_SCOPE
    scope_type missing or not one of
      "user" / "cost_centre" / "organization" -> INVALID_SCOPE_TYPE
    scope_type == "user" but no (non-empty,
      string) scope_user_id                -> MISSING_SCOPE_USER_ID
    scope_type == "cost_centre" but no
      (non-empty, string) cost_centre      -> MISSING_COST_CENTRE

This module does NOT implement role-based authorization rules (it does not
decide that an "Employee" gets user scope, or that a "Manager" gets
cost_centre scope -- Auth/RBAC already decided that). It only validates
that the scope dict it was handed is well-formed and applies it.

--------------------------------------------------------------------------
QUERY SCOPE SECURITY
--------------------------------------------------------------------------
Every SQL statement filters expenses/budgets using ONLY the trusted
`authorized_scope` (via _scope_where_clause / _require_cost_centre_budget_scope),
through parameterized SQL (never string interpolation). No query in this
file EVER uses `query["user_scope"]`, `query["user_id"]`, or any other
query-supplied field to filter the database.

`query["user_scope"]`, when the compiler supplies it, is used for exactly
one thing: a consistency check against the trusted `authorized_scope`. The
trusted scope always wins; a conflicting query is rejected rather than
widened or narrowed:

    authorized_scope scope_type == "user"
        -> query user_scope, if present, must equal scope_user_id
    authorized_scope scope_type == "cost_centre"
        -> query user_scope, if present, must equal cost_centre
    authorized_scope scope_type == "organization"
        -> ANY query user_scope value is rejected outright -- an
           organization-wide authorization must never be narrowed or
           replaced by an untrusted query-supplied scope

A mismatch (or any user_scope at all under organization scope) is rejected
with USER_SCOPE_CONFLICT before any intent-specific logic runs. Fields like
`query["user_id"]` are never read by this module at all -- there is nothing
for them to override, by construction, not by a special-cased check.

--------------------------------------------------------------------------
BUDGET SCOPE
--------------------------------------------------------------------------
database/models.py's `budgets` table is cost-centre based only:

    budget_id, cost_centre, category, amount, period_start, period_end

There is no user-level or organization-level budget dimension. So for
remaining_budget/burn_rate:

    scope_type == "cost_centre" -> budget lookup uses the trusted
                                     cost_centre, exactly as before.
    scope_type == "user"         -> BUDGET_SCOPE_UNSUPPORTED. This file does
                                     NOT invent a user-level budget.
    scope_type == "organization" -> BUDGET_SCOPE_UNSUPPORTED. This file does
                                     NOT invent an organization-wide budget
                                     and does NOT treat a fake cost_centre
                                     "ALL" as real. If the schema is later
                                     extended with an organization-level
                                     budget concept, this is where that
                                     would be wired in -- not before.

--------------------------------------------------------------------------
DATE HANDLING
--------------------------------------------------------------------------
The Query Compiler schema types date_range_start/date_range_end as
Optional[date] (python datetime.date / datetime.datetime). SQLite stores
expense dates as 'YYYY-MM-DD' strings. _normalize_date() converts a date to
that representation before it is ever used -- always as a bound SQL
parameter, never interpolated into the SQL text. As a defensive fallback it
also accepts a plain string, but does NOT trust it blindly: the string must
first match _DATE_STRING_RE (^\\d{4}-\\d{2}-\\d{2}$) exactly, then parse as a
real calendar date via datetime.strptime (which also catches impossible
dates such as '2026-02-30'). Any other type, a malformed string, or a
string that isn't an actual date is rejected with a clean INVALID_DATE
failure rather than letting a bad value reach SQL.

--------------------------------------------------------------------------
CATEGORY VALUES (e.g. "Snacks")
--------------------------------------------------------------------------
The Query Compiler's canonical category list is not the same as
database/ingestion.py's current ALLOWED_CATEGORIES (e.g. "Snacks" is not
yet an ingestable category). This file does not validate `category` against
any allow-list and does not modify database/ingestion.py. It simply filters
using whatever category string the query supplies; if no expense/budget
rows exist for that category, the normal empty-result or BUDGET_NOT_FOUND
behavior applies -- never a crash, a silent 0, or an invented budget.
"""

from __future__ import annotations

import datetime
import re
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence

from database.connection import get_connection
from calculation.formulas import (
    calculate_total_expenses,
    calculate_category_spending,
    calculate_expense_count,
    calculate_top_transactions,
    calculate_remaining_budget,
    calculate_burn_rate,
)

# The six intents the Query Compiler actually emits.
SUPPORTED_INTENTS = {
    "sum_expenses",
    "category_breakdown",
    "top_transactions",
    "count_expenses",
    "remaining_budget",
    "source_lookup",
}

# Extra engine-only capability, not part of the compiler contract (see
# module docstring). Kept separate so it's obvious it isn't one of the six.
_EXTRA_INTENTS = {"burn_rate"}

_ALL_INTENTS = SUPPORTED_INTENTS | _EXTRA_INTENTS

DEFAULT_TOP_TRANSACTIONS_LIMIT = 5

# Strict shape check applied to a date string BEFORE it is parsed by
# datetime.strptime() in _normalize_date() -- see that function's docstring.
_DATE_STRING_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# The three scope_type values auth/rbac.py's get_authorized_scope() can
# return (see AUTHORIZED SCOPE in the module docstring).
_SCOPE_TYPES = {"user", "cost_centre", "organization"}


class EngineError(Exception):
    """
    Raised for any engine-level failure that should become a clean
    machine-readable failure result rather than an uncaught exception or a
    fabricated success. Carries a short machine-readable `status` code plus
    a human-readable `message`.
    """

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

def run_calculation(query: Mapping[str, Any], authorized_scope: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Run one calculation-engine operation.

    Args:
        query: structured query dict produced by the Query Compiler. Must
            contain "intent" (see SUPPORTED_INTENTS). May contain
            "user_scope", "category", "date_range_start", "date_range_end",
            "limit" (top_transactions only) and "currency".
        authorized_scope: the trusted scope dict returned by
            auth.get_authorized_scope() -- see AUTHORIZED SCOPE in the
            module docstring for its three possible shapes. This is the
            ONLY source of the security scope used to filter the database.
            `query["user_scope"]`, if present, is checked for consistency
            against this value but never used to filter -- see QUERY SCOPE
            SECURITY in the module docstring.

    Returns:
        A result dict. Always contains "status", "result", "currency" and
        "source_rows". See the RESULT CONTRACT section of the module
        docstring for the full shape and failure statuses.
    """
    if not isinstance(query, Mapping):
        return _failure("INVALID_QUERY", "query must be a mapping (e.g. a dict).")

    # Scope validation and the query-scope conflict check both run before
    # intent validation/dispatch: the engine fails closed on a malformed or
    # conflicting scope regardless of what intent was requested.
    try:
        scope = _validate_scope(authorized_scope)
        _check_query_scope_conflict(query, scope)
    except EngineError as exc:
        return _failure(exc.status, exc.message)

    intent = query.get("intent")
    if intent not in _ALL_INTENTS:
        return _failure(
            "UNKNOWN_INTENT",
            f"Unsupported intent: {intent!r}. Supported intents: {sorted(SUPPORTED_INTENTS)}",
        )

    try:
        with get_connection() as conn:
            return _dispatch(intent, conn, query, scope)
    except EngineError as exc:
        return _failure(exc.status, exc.message)
    except (ValueError, TypeError) as exc:
        # Raised by calculation/formulas.py for bad numeric input, a bad
        # limit, etc. Surfaced as a clean status instead of a raw traceback.
        return _failure("CALCULATION_ERROR", str(exc))
    except sqlite3.Error:
        # Never leak raw database exception details to the caller.
        return _failure("DATABASE_ERROR", "A database error occurred while running the calculation.")


def _dispatch(
    intent: str,
    conn: sqlite3.Connection,
    query: Mapping[str, Any],
    scope: Dict[str, Any],
) -> Dict[str, Any]:
    """Route to the handler for one intent. Assumes intent is already valid."""
    if intent == "sum_expenses":
        return _handle_sum_expenses(conn, query, scope)
    if intent == "category_breakdown":
        return _handle_category_breakdown(conn, query, scope)
    if intent == "count_expenses":
        return _handle_count_expenses(conn, query, scope)
    if intent == "top_transactions":
        return _handle_top_transactions(conn, query, scope)
    if intent == "remaining_budget":
        return _handle_remaining_budget(conn, query, scope)
    if intent == "burn_rate":
        return _handle_burn_rate(conn, query, scope)
    if intent == "source_lookup":
        return _handle_source_lookup(conn, query, scope)
    # Unreachable: run_calculation() already validated intent against
    # _ALL_INTENTS before calling _dispatch().
    raise EngineError("UNKNOWN_INTENT", f"Unsupported intent: {intent!r}")


# --------------------------------------------------------------------------
# Scope validation and application (AUTH BOUNDARY)
# --------------------------------------------------------------------------

def _validate_scope(authorized_scope: Any) -> Dict[str, Any]:
    """
    Validate the trusted authorized_scope dict handed to run_calculation()
    (the dict shape auth.get_authorized_scope() returns -- see AUTHORIZED
    SCOPE in the module docstring). Fails closed: raises EngineError on any
    problem rather than guessing or defaulting to a wide scope.

    Returns a normalized dict containing only the fields this module
    actually uses:
        {"scope_type": "user", "scope_user_id": "..."}
        {"scope_type": "cost_centre", "cost_centre": "..."}
        {"scope_type": "organization"}

    Extra fields on the input (user_id, role, ...) are read nowhere in this
    module -- they are simply not copied into the returned dict.
    """
    if not authorized_scope or not isinstance(authorized_scope, Mapping):
        raise EngineError(
            "MISSING_AUTHORIZED_SCOPE",
            "authorized_scope is required and must be a non-empty mapping "
            "(the dict returned by auth.get_authorized_scope()).",
        )

    scope_type = authorized_scope.get("scope_type")
    if scope_type not in _SCOPE_TYPES:
        raise EngineError(
            "INVALID_SCOPE_TYPE",
            f"authorized_scope['scope_type'] must be one of {sorted(_SCOPE_TYPES)}, got {scope_type!r}.",
        )

    if scope_type == "user":
        scope_user_id = authorized_scope.get("scope_user_id")
        if not scope_user_id or not isinstance(scope_user_id, str):
            raise EngineError(
                "MISSING_SCOPE_USER_ID",
                "authorized_scope['scope_user_id'] is required and must be a "
                "non-empty string when scope_type is 'user'.",
            )
        return {"scope_type": "user", "scope_user_id": scope_user_id}

    if scope_type == "cost_centre":
        cost_centre = authorized_scope.get("cost_centre")
        if not cost_centre or not isinstance(cost_centre, str):
            raise EngineError(
                "MISSING_COST_CENTRE",
                "authorized_scope['cost_centre'] is required and must be a "
                "non-empty string when scope_type is 'cost_centre'.",
            )
        return {"scope_type": "cost_centre", "cost_centre": cost_centre}

    # scope_type == "organization": no additional field required.
    return {"scope_type": "organization"}


def _check_query_scope_conflict(query: Mapping[str, Any], scope: Dict[str, Any]) -> None:
    """
    Reject the request if query['user_scope'] (untrusted, Query-Compiler-
    supplied) conflicts with the trusted `scope`. Never uses
    query['user_scope'] to filter anything -- it only decides whether to
    refuse the request. See QUERY SCOPE SECURITY in the module docstring.
    """
    query_user_scope = query.get("user_scope")
    if query_user_scope is None:
        return

    scope_type = scope["scope_type"]
    if scope_type == "organization":
        # An organization-wide authorization must never be narrowed or
        # replaced by an untrusted query-supplied scope -- any value here
        # is rejected outright, not just a mismatching one.
        raise EngineError(
            "USER_SCOPE_CONFLICT",
            "query user_scope must not be supplied when authorized_scope is "
            "organization-wide; request rejected.",
        )

    trusted_value = scope["scope_user_id"] if scope_type == "user" else scope["cost_centre"]
    if query_user_scope != trusted_value:
        raise EngineError(
            "USER_SCOPE_CONFLICT",
            f"query user_scope {query_user_scope!r} does not match the authorized scope; request rejected.",
        )


def _scope_where_clause(scope: Dict[str, Any]) -> tuple:
    """
    Build the trusted scope's restriction on the `expenses` table as a
    (sql_fragment, params) pair, always parameterized:

        user scope         -> (" AND user_id = ?", [scope_user_id])
        cost_centre scope   -> (" AND cost_centre = ?", [cost_centre])
        organization scope   -> ("", []) -- no artificial restriction; the
                                 whole organization's expenses are in scope

    The scope value is never interpolated into SQL text.
    """
    scope_type = scope["scope_type"]
    if scope_type == "user":
        return " AND user_id = ?", [scope["scope_user_id"]]
    if scope_type == "cost_centre":
        return " AND cost_centre = ?", [scope["cost_centre"]]
    return "", []


def _require_cost_centre_budget_scope(scope: Dict[str, Any], purpose: str) -> str:
    """
    Budgets are defined per cost_centre only (database/models.py's budgets
    table has no user or organization dimension). Only a cost_centre scope
    (Manager) can resolve a budget deterministically from the existing
    schema, so this returns the trusted cost_centre string for that case.
    For any other scope_type it raises a clear BUDGET_SCOPE_UNSUPPORTED
    EngineError explaining exactly why -- it never invents a user-level or
    organization-level budget, and never uses a fake cost_centre like "ALL".
    """
    scope_type = scope["scope_type"]
    if scope_type == "cost_centre":
        return scope["cost_centre"]
    if scope_type == "user":
        raise EngineError(
            "BUDGET_SCOPE_UNSUPPORTED",
            f"Cannot compute {purpose}: budgets are tracked per cost centre in "
            "the existing schema, not per user; a user-scoped authorization "
            "cannot resolve a budget.",
        )
    # organization
    raise EngineError(
        "BUDGET_SCOPE_UNSUPPORTED",
        f"Cannot compute {purpose}: the existing schema has no organization-wide "
        "budget (budgets are cost-centre based); an organization-wide budget "
        "cannot be safely determined without inventing one.",
    )


# --------------------------------------------------------------------------
# Query-field helpers
# --------------------------------------------------------------------------

def _normalize_date(value: Any, label: str) -> Optional[str]:
    """
    Normalize a date-like query value to the 'YYYY-MM-DD' string the
    database stores.

    Accepts: None, datetime.date, datetime.datetime (converted via
    .date()), or a str. The Query Compiler schema types these fields as
    Optional[date], but this stays defensive in case a caller passes a
    string instead. A string is NOT accepted at face value -- it must first
    match _DATE_STRING_RE (^\\d{4}-\\d{2}-\\d{2}$) exactly, so loosely-shaped
    input like '2026-9-1' (strptime would otherwise accept the missing zero
    padding) or anything with extra characters is rejected before parsing
    even starts; only then is it parsed with datetime.strptime, which
    rejects impossible calendar dates like '2026-02-30'. Anything else --
    the wrong type, a string that fails the regex, or one that fails to
    parse -- is rejected with a clean INVALID_DATE EngineError instead of
    letting a malformed value reach SQL. The result is always used as a
    bound parameter -- never interpolated into SQL text.
    """
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, str):
        if not _DATE_STRING_RE.match(value):
            raise EngineError(
                "INVALID_DATE",
                f"{label} must be a valid 'YYYY-MM-DD' date, got {value!r}",
            )
        try:
            parsed = datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise EngineError(
                "INVALID_DATE",
                f"{label} must be a valid 'YYYY-MM-DD' date, got {value!r}",
            )
        return parsed.isoformat()
    raise EngineError(
        "INVALID_DATE",
        f"{label} must be a date or a 'YYYY-MM-DD' string, got {type(value).__name__}: {value!r}",
    )


def _extract_filters(query: Mapping[str, Any]) -> tuple:
    """
    Pull the common filter fields off a Query Compiler query object:
    category, date_range_start, date_range_end (normalized to
    'YYYY-MM-DD'), and currency. Shared by every intent handler so the
    field names are read in exactly one place.
    """
    category = query.get("category")
    date_start = _normalize_date(query.get("date_range_start"), "date_range_start")
    date_end = _normalize_date(query.get("date_range_end"), "date_range_end")
    currency = query.get("currency")
    return category, date_start, date_end, currency


# --------------------------------------------------------------------------
# Database retrieval helpers (DATABASE -> FILTER)
# --------------------------------------------------------------------------

def _fetch_expenses(
    conn: sqlite3.Connection,
    scope: Dict[str, Any],
    category: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve expense rows restricted by the trusted `scope` (see
    _scope_where_clause), with optional filters, and convert them from
    sqlite3.Row to plain dict (required by calculation/formulas.py). Date
    range is inclusive on both ends. All filter values (category/
    date_start/date_end/currency) must already be plain strings -- callers
    normalize dates via _normalize_date() first.
    """
    scope_sql, scope_params = _scope_where_clause(scope)
    sql = "SELECT * FROM expenses WHERE 1=1" + scope_sql
    params: List[Any] = list(scope_params)

    if category is not None:
        sql += " AND category = ?"
        params.append(category)
    if date_start is not None:
        sql += " AND date >= ?"
        params.append(date_start)
    if date_end is not None:
        sql += " AND date <= ?"
        params.append(date_end)
    if currency is not None:
        sql += " AND currency = ?"
        params.append(currency)

    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def _fetch_budget(
    conn: sqlite3.Connection,
    cost_centre: str,
    category: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    purpose: str = "remaining budget",
) -> Dict[str, Any]:
    """
    Locate the single applicable budget row for `cost_centre` (already
    resolved from the trusted scope by _require_cost_centre_budget_scope --
    budgets are cost-centre based only, so this never takes a scope dict
    directly).

    `category` is REQUIRED: budgets are stored per (cost_centre, category),
    so a budget cannot be identified without one.

    If date_start/date_end are supplied, they must match the budget row's
    period_start/period_end EXACTLY. INTEGRATION_CONTRACT.md does not define
    overlapping/partial-period budget semantics, so engine.py does not guess
    at that -- the caller must name the exact period it wants. If they are
    omitted, exactly one budget row must exist for the cost_centre/category
    pair, or the lookup is ambiguous.

    Never invents a budget. Raises EngineError on any failure to find
    exactly one matching row. `purpose` (e.g. "remaining budget" or
    "burn rate") is folded into the BUDGET_NOT_FOUND message so it clearly
    names the missing category, matching the required message shape:
    "Cannot compute <purpose>: no budget allocated for <category>".
    """
    if not category:
        raise EngineError(
            "MISSING_CATEGORY",
            "A 'category' is required to identify the applicable budget.",
        )

    sql = "SELECT * FROM budgets WHERE cost_centre = ? AND category = ?"
    params: List[Any] = [cost_centre, category]
    if date_start is not None:
        sql += " AND period_start = ?"
        params.append(date_start)
    if date_end is not None:
        sql += " AND period_end = ?"
        params.append(date_end)

    rows = conn.execute(sql, params).fetchall()
    budgets = [dict(row) for row in rows]

    if not budgets:
        # Required message shape, e.g.:
        #   "Cannot compute remaining budget: no budget allocated for Snacks"
        raise EngineError(
            "BUDGET_NOT_FOUND",
            f"Cannot compute {purpose}: no budget allocated for {category}",
        )
    if len(budgets) > 1:
        raise EngineError(
            "AMBIGUOUS_BUDGET",
            f"{len(budgets)} budgets match cost_centre={cost_centre!r}, "
            f"category={category!r}; specify date_range_start/date_range_end to select exactly one period.",
        )
    return budgets[0]


# --------------------------------------------------------------------------
# Currency resolution (no conversion -- see module docstring)
# --------------------------------------------------------------------------

def _resolve_currency(records: Sequence[Dict[str, Any]], requested_currency: Optional[str]) -> Optional[str]:
    """
    Decide the "currency" value for the output.

    - If the caller explicitly filtered by currency, echo that back
      (even if zero rows matched -- the caller already named it).
    - Otherwise, every record must share one currency: combining different
      currencies into a single number (or a single ranked/labeled list)
      would be misleading, since this engine performs no conversion.
      Raises EngineError if more than one currency is present.
    - If there are no records and no explicit filter, the currency is
      unknown and reported as None rather than guessed.
    """
    if requested_currency is not None:
        return requested_currency

    currencies = {record["currency"] for record in records if "currency" in record}
    if len(currencies) > 1:
        raise EngineError(
            "MIXED_CURRENCY",
            f"Matching records span multiple currencies ({sorted(currencies)}); "
            "supply an explicit 'currency' filter to get a meaningful result.",
        )
    if len(currencies) == 1:
        return next(iter(currencies))
    return None


# --------------------------------------------------------------------------
# Shared result builders
# --------------------------------------------------------------------------

def _build_filters(
    scope: Dict[str, Any],
    category: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    currency: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a human-readable record of which filters were actually applied.
    "scope" reports the resolved, trusted scope dict (scope_type plus its
    one required field) rather than a "cost_centre" key, since that
    wouldn't make sense for user/organization scope.
    """
    filters: Dict[str, Any] = {"scope": dict(scope)}
    if category is not None:
        filters["category"] = category
    if date_start is not None or date_end is not None:
        filters["date_range"] = f"{date_start or '...'} to {date_end or '...'}"
    if currency is not None:
        filters["currency"] = currency
    if limit is not None:
        filters["limit"] = limit
    return filters


def _success(
    result: Any,
    source_rows: List[str],
    currency: Optional[str],
    **extra: Any,
) -> Dict[str, Any]:
    """Build a SUCCESS result, keeping the contract's core 3 keys plus status."""
    output: Dict[str, Any] = {
        "status": "SUCCESS",
        "result": result,
        "currency": currency,
        "source_rows": source_rows,
    }
    output.update(extra)
    return output


def _failure(status: str, message: str, **extra: Any) -> Dict[str, Any]:
    """Build a FAILURE result. Never fabricates a result value on failure."""
    output: Dict[str, Any] = {
        "status": status,
        "result": None,
        "currency": None,
        "source_rows": [],
        "error": message,
    }
    output.update(extra)
    return output


# --------------------------------------------------------------------------
# Intent handlers -- each is DATABASE -> FILTER -> FORMULA -> RESULT
# --------------------------------------------------------------------------

def _handle_sum_expenses(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    category, date_start, date_end, currency = _extract_filters(query)

    expenses = _fetch_expenses(conn, scope, category, date_start, date_end, currency)

    # Validate currency compatibility BEFORE any financial math. A SUM across
    # mixed currencies would be a real number that is mathematically wrong,
    # so MIXED_CURRENCY must be raised before calculate_total_expenses() runs
    # -- never after.
    resolved_currency = _resolve_currency(expenses, currency)
    total = calculate_total_expenses(expenses)  # all math done by formulas.py
    source_rows = [e["expense_id"] for e in expenses]

    return _success(
        result=total,
        source_rows=source_rows,
        currency=resolved_currency,
        formula="SUM(amount)",
        filters=_build_filters(scope, category, date_start, date_end, currency),
        row_count=len(expenses),
    )


def _handle_category_breakdown(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    category, date_start, date_end, currency = _extract_filters(query)

    expenses = _fetch_expenses(conn, scope, category, date_start, date_end, currency)

    # Validate currency compatibility BEFORE any financial math -- a
    # per-category SUM across mixed currencies would be mathematically
    # wrong, so MIXED_CURRENCY must be raised before
    # calculate_category_spending() runs.
    resolved_currency = _resolve_currency(expenses, currency)
    breakdown = calculate_category_spending(expenses)
    source_rows = [e["expense_id"] for e in expenses]

    return _success(
        result=breakdown,
        source_rows=source_rows,
        currency=resolved_currency,
        formula="SUM(amount) GROUP BY category",
        filters=_build_filters(scope, category, date_start, date_end, currency),
        row_count=len(expenses),
    )


def _handle_count_expenses(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    category, date_start, date_end, currency = _extract_filters(query)

    expenses = _fetch_expenses(conn, scope, category, date_start, date_end, currency)
    count = calculate_expense_count(expenses)
    source_rows = [e["expense_id"] for e in expenses]

    return _success(
        result=count,
        # A count is not a monetary sum, so mixed currencies among the
        # counted rows don't make the number misleading -- no mixed-
        # currency check is applied here, unlike the sum-based intents.
        currency=currency,
        source_rows=source_rows,
        formula="COUNT(*)",
        filters=_build_filters(scope, category, date_start, date_end, currency),
        row_count=count,
    )


def _handle_top_transactions(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    category, date_start, date_end, currency = _extract_filters(query)
    limit = query.get("limit", DEFAULT_TOP_TRANSACTIONS_LIMIT)  # formulas.py validates this

    expenses = _fetch_expenses(conn, scope, category, date_start, date_end, currency)

    # Validate currency compatibility BEFORE ranking. "Top N by amount"
    # across mixed currencies would rank a USD figure against an INR figure
    # as if they were the same unit -- that is exactly the kind of
    # misleading combination this engine must not produce silently, so the
    # check runs over the full candidate set, before calling
    # calculate_top_transactions(), not just over whichever records happen
    # to end up in the top N.
    resolved_currency = _resolve_currency(expenses, currency)
    top_records = calculate_top_transactions(expenses, limit)  # sorting + limit validation done by formulas.py
    source_rows = [r["expense_id"] for r in top_records]

    return _success(
        result=top_records,  # full records preserved -- no evidence lost
        source_rows=source_rows,
        currency=resolved_currency,
        formula=f"TOP {limit} BY amount DESC",
        filters=_build_filters(scope, category, date_start, date_end, currency, limit),
        row_count=len(expenses),
    )


def _handle_remaining_budget(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    category, date_start, date_end, currency = _extract_filters(query)

    # Budgets are cost-centre based only -- raises BUDGET_SCOPE_UNSUPPORTED
    # for user/organization scope rather than inventing a budget (see
    # BUDGET SCOPE in the module docstring).
    cost_centre = _require_cost_centre_budget_scope(scope, purpose="remaining budget")

    # Never invents a budget -- raises BUDGET_NOT_FOUND / AMBIGUOUS_BUDGET
    # via EngineError, caught by run_calculation(). Message names the
    # missing category explicitly, e.g.:
    #   "Cannot compute remaining budget: no budget allocated for Snacks"
    budget = _fetch_budget(
        conn, cost_centre, category, date_start, date_end, purpose="remaining budget"
    )

    # "Remaining budget" means what's left of THIS budget's own period, so
    # spend is measured over budget["period_start"]..budget["period_end"],
    # not any caller-supplied range (which was only used to pick the budget).
    # `scope` here is the same cost_centre scope the budget was resolved
    # from, so the expense restriction and the budget's cost centre always
    # agree -- there is no separate "which cost centre's expenses" question.
    expenses = _fetch_expenses(
        conn,
        scope,
        category,
        date_start=budget["period_start"],
        date_end=budget["period_end"],
        currency=currency,
    )

    # Validate expense-currency compatibility BEFORE any financial math.
    # calculate_total_expenses() must not run over a mixed-currency set.
    resolved_currency = _resolve_currency(expenses, currency)
    spend = calculate_total_expenses(expenses)
    remaining = calculate_remaining_budget(budget["amount"], spend)  # subtraction done by formulas.py
    source_rows = [e["expense_id"] for e in expenses]

    return _success(
        result=remaining,
        source_rows=source_rows,
        # "currency" describes the expense side only (the side that
        # actually has a currency column). The budgets table has NO
        # currency column (budget_id, cost_centre, category, amount,
        # period_start, period_end) -- engine.py never invents one or
        # assumes the budget is denominated in whatever currency the
        # expenses happen to use. budget_currency is always explicitly
        # None rather than silently reusing "currency" for the budget too.
        currency=resolved_currency,
        budget_currency=None,
        formula="budget_amount - SUM(amount)",
        filters=_build_filters(
            scope, category, budget["period_start"], budget["period_end"], currency
        ),
        row_count=len(expenses),
        budget_id=budget["budget_id"],
        budget_amount=budget["amount"],
        spend=spend,
    )


def _handle_burn_rate(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extra, non-compiler engine capability (see module docstring). Not one of
    the six Query Compiler intents, but kept available and consistent with
    remaining_budget's scope/currency/missing-budget handling.
    """
    category, date_start, date_end, currency = _extract_filters(query)

    cost_centre = _require_cost_centre_budget_scope(scope, purpose="burn rate")

    budget = _fetch_budget(
        conn, cost_centre, category, date_start, date_end, purpose="burn rate"
    )

    expenses = _fetch_expenses(
        conn,
        scope,
        category,
        date_start=budget["period_start"],
        date_end=budget["period_end"],
        currency=currency,
    )

    # Validate expense-currency compatibility BEFORE any financial math.
    # Neither calculate_total_expenses() nor calculate_burn_rate() may run
    # over a mixed-currency expense set.
    resolved_currency = _resolve_currency(expenses, currency)
    spend = calculate_total_expenses(expenses)

    try:
        rate = calculate_burn_rate(spend, budget["amount"])  # division done by formulas.py
    except ValueError as exc:
        # Turn formulas.py's zero-budget ValueError into a clean status
        # instead of letting it bubble up as a generic CALCULATION_ERROR.
        raise EngineError("BURN_RATE_UNDEFINED", str(exc)) from exc

    source_rows = [e["expense_id"] for e in expenses]

    return _success(
        result=rate,
        source_rows=source_rows,
        # See _handle_remaining_budget: budgets have no currency column, so
        # "currency" describes the expense side only, and budget_currency
        # is always explicitly None rather than assumed.
        currency=resolved_currency,
        budget_currency=None,
        formula="(SUM(amount) / budget_amount) * 100",
        filters=_build_filters(
            scope, category, budget["period_start"], budget["period_end"], currency
        ),
        row_count=len(expenses),
        budget_id=budget["budget_id"],
        budget_amount=budget["amount"],
        spend=spend,
    )


def _handle_source_lookup(
    conn: sqlite3.Connection, query: Mapping[str, Any], scope: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Filtered source-row lookup/retrieval. This intent takes no expense_ids
    list (the compiler schema has none) -- it uses the same filters as
    every other intent (category, date_range_start/end, currency),
    restricted to the trusted `scope` exactly like _fetch_expenses().
    Returns the matching expense records as "result" and their expense_id
    values as "source_rows". Records outside the authorized scope can never
    be returned, since the query is scoped the same way as every other
    handler in this file.

    If an explicit currency is supplied, it is applied as a real SQL filter
    (via _fetch_expenses -- parameterized, never string-interpolated), so
    only matching rows are returned; "currency" in the result reflects what
    was actually fetched, not merely what was requested. If no currency is
    supplied, the existing mixed-currency detection (_resolve_currency)
    still applies: a result spanning more than one currency is refused
    rather than silently mixed.
    """
    category, date_start, date_end, currency = _extract_filters(query)

    records = _fetch_expenses(conn, scope, category, date_start, date_end, currency)

    # Validate currency compatibility before returning results as a single
    # currency-labeled set, for the same reason as the other monetary/
    # evidence-bearing intents.
    resolved_currency = _resolve_currency(records, currency)
    source_rows = [r["expense_id"] for r in records]

    return _success(
        result=records,
        source_rows=source_rows,
        currency=resolved_currency,
        formula="SELECT * (authorized, filtered)",
        filters=_build_filters(scope, category, date_start, date_end, currency),
        row_count=len(records),
    )
