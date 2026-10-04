"""
calculation/engine.py

The Deterministic Calculation Engine for L.E.D.G.E.R.

Responsibility (per INTEGRATION_CONTRACT.md, section 6):

    authorized query -> Database -> Deterministic Calculation -> Audit/Frontend

This module ONLY does: DATABASE -> FILTER -> FORMULA -> RESULT.
It never performs financial arithmetic itself -- every number in a result
comes from calculation/formulas.py. It never authenticates or authorizes a
user -- it only accepts an already-authorized cost centre as a trusted input.

--------------------------------------------------------------------------
COMPATIBILITY NOTE (auth/ and query/ do not exist yet)
--------------------------------------------------------------------------
This module does NOT import from an `auth` or `query` package, because
neither exists in the repository yet. Instead it exposes one plain entry
point:

    run_calculation(query: Mapping[str, Any], authorized_cost_centre: str) -> dict

When auth/ and query/ are implemented, the caller (Streamlit UI or a small
routing layer) is expected to:
  1. Authenticate the user and resolve their authorized_cost_centre via the
     future auth/rbac module.
  2. Compile the natural-language question into the structured `query` dict
     via the future query-compiler module.
  3. Call run_calculation(query, authorized_cost_centre) with both.

engine.py never reads a cost-centre-shaped value out of `query` itself --
`authorized_cost_centre` is a separate function argument, sourced only from
the trusted caller, so nothing inside `query` can ever override it.

--------------------------------------------------------------------------
STRUCTURED QUERY -- CONTRACT FIELDS vs ENGINE-LEVEL FIELDS
--------------------------------------------------------------------------
Fields defined by INTEGRATION_CONTRACT.md section 2/3:
    intent        (str, required)  -- see SUPPORTED_INTENTS below
    category      (str, optional)
    date_start    (str "YYYY-MM-DD", optional)
    date_end      (str "YYYY-MM-DD", optional)

Engine-level fields (NOT part of INTEGRATION_CONTRACT.md -- documented here
as an implementation detail this engine currently relies on):
    top_n         (int, optional)  -- required only by "top_transactions"
    currency      (str, optional)  -- one of INR/USD/EUR; filters expenses,
                                       never converts between currencies
    expense_ids   (list[str], required only by "source_rows")

The contract's own example query has no "cost_centre" field, and engine.py
never looks for one -- the authorized cost centre always comes from the
authorized_cost_centre argument.

--------------------------------------------------------------------------
SUPPORTED INTENTS
--------------------------------------------------------------------------
INTEGRATION_CONTRACT.md only shows "sum_expenses" as an example intent. The
remaining names below were chosen (per the task's naming preference) to
cover the other calculation-engine requirements. No other intents/financial
calculations are supported.

    sum_expenses        -> calculate_total_expenses()
    category_spending   -> calculate_category_spending()
    expense_count        -> calculate_expense_count()
    top_transactions     -> calculate_top_transactions()
    remaining_budget      -> calculate_remaining_budget()
    burn_rate             -> calculate_burn_rate()
    source_rows           -> direct lookup of specific expense_ids (no formula
                              math involved; pure evidence retrieval)

--------------------------------------------------------------------------
RESULT CONTRACT
--------------------------------------------------------------------------
INTEGRATION_CONTRACT.md section 4 defines the core output shape:

    {"result": ..., "currency": "INR", "source_rows": [...]}

Every result from run_calculation() keeps these three keys. Additional
metadata keys (status, formula, filters, row_count, budget_id, ...) are
appended without removing or renaming the core three, so contract-compatible
callers that only read result/currency/source_rows keep working unchanged.

CURRENCY FIELD: this engine performs NO currency conversion (per the schema
and ingestion contract, there is no exchange-rate field anywhere). If the
caller filters by an explicit "currency", the expense rows are filtered by
it first, then validated, then a formula runs. If no filter is given, the
matching expense rows are validated BEFORE any formula call: if they span
more than one currency, summing/ranking them would silently produce a
misleading number, so the engine returns MIXED_CURRENCY and never calls
calculate_total_expenses() / calculate_category_spending() /
calculate_top_transactions() / calculate_burn_rate() over that mixed set.
This validate-before-calculate ordering applies to every monetary intent
(sum_expenses, category_spending, remaining_budget, burn_rate) and to
top_transactions (ranking mixed-currency amounts by raw value is an equally
misleading combination). expense_count is a row count, not a monetary
value, so no currency check applies to it. If no currency filter is given
and every matching row shares one currency, that currency is used. If there
are no matching rows and no filter, the currency is reported as None
(unknown, not guessed).

BUDGET CURRENCY: the budgets table has NO currency column (budget_id,
cost_centre, category, amount, period_start, period_end). For
remaining_budget and burn_rate, the top-level "currency" field describes
the expense side only (the side that actually has currency data); engine.py
never assumes the budget amount shares that currency. Both intents also
return an explicit "budget_currency": None, so a caller can never mistake
"currency" for a verified property of the budget amount.

FAILURE SHAPE: INTEGRATION_CONTRACT.md does not define a failure shape (only
a success example). Failures use the same three core keys, with
result=None, source_rows=[], plus "status" and "error" describing why:

    {"status": "BUDGET_NOT_FOUND", "result": None, "currency": None,
     "source_rows": [], "error": "..."}

--------------------------------------------------------------------------
SECURITY
--------------------------------------------------------------------------
Every SQL statement filters expenses/budgets by `cost_centre = ?` using the
authorized_cost_centre argument, via parameterized SQL (never string
interpolation). No query in this file ever reads a cost-centre value out of
the `query` dict.
"""

from __future__ import annotations

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

SUPPORTED_INTENTS = {
    "sum_expenses",
    "category_spending",
    "expense_count",
    "top_transactions",
    "remaining_budget",
    "burn_rate",
    "source_rows",
}


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

def run_calculation(query: Mapping[str, Any], authorized_cost_centre: str) -> Dict[str, Any]:
    """
    Run one calculation-engine operation.

    Args:
        query: structured query dict. Must contain "intent" (see
            SUPPORTED_INTENTS). May contain the contract fields
            (category, date_start, date_end) and, where a specific intent
            needs them, the engine-level fields documented at the top of
            this file (top_n, currency, expense_ids).
        authorized_cost_centre: the cost centre the caller is authorized
            for, resolved by the (future) auth/RBAC layer. This is the ONLY
            source of the security scope -- nothing inside `query` is ever
            used for authorization, so a caller cannot override it by
            putting a cost_centre-shaped value inside the query dict.

    Returns:
        A result dict. Always contains "status", "result", "currency" and
        "source_rows". See the RESULT CONTRACT section of the module
        docstring for the full shape and failure statuses.
    """
    if not authorized_cost_centre or not isinstance(authorized_cost_centre, str):
        return _failure(
            "MISSING_AUTHORIZED_SCOPE",
            "authorized_cost_centre is required and must be a non-empty string.",
        )

    if not isinstance(query, Mapping):
        return _failure("INVALID_QUERY", "query must be a mapping (e.g. a dict).")

    intent = query.get("intent")
    if intent not in SUPPORTED_INTENTS:
        return _failure(
            "UNKNOWN_INTENT",
            f"Unsupported intent: {intent!r}. Supported intents: {sorted(SUPPORTED_INTENTS)}",
        )

    try:
        with get_connection() as conn:
            return _dispatch(intent, conn, query, authorized_cost_centre)
    except EngineError as exc:
        return _failure(exc.status, exc.message)
    except (ValueError, TypeError) as exc:
        # Raised by calculation/formulas.py for bad numeric input, a bad
        # top_n, etc. Surfaced as a clean status instead of a raw traceback.
        return _failure("CALCULATION_ERROR", str(exc))
    except sqlite3.Error:
        # Never leak raw database exception details to the caller.
        return _failure("DATABASE_ERROR", "A database error occurred while running the calculation.")


def _dispatch(
    intent: str,
    conn: sqlite3.Connection,
    query: Mapping[str, Any],
    authorized_cost_centre: str,
) -> Dict[str, Any]:
    """Route to the handler for one intent. Assumes intent is already valid."""
    if intent == "sum_expenses":
        return _handle_sum_expenses(conn, query, authorized_cost_centre)
    if intent == "category_spending":
        return _handle_category_spending(conn, query, authorized_cost_centre)
    if intent == "expense_count":
        return _handle_expense_count(conn, query, authorized_cost_centre)
    if intent == "top_transactions":
        return _handle_top_transactions(conn, query, authorized_cost_centre)
    if intent == "remaining_budget":
        return _handle_remaining_budget(conn, query, authorized_cost_centre)
    if intent == "burn_rate":
        return _handle_burn_rate(conn, query, authorized_cost_centre)
    if intent == "source_rows":
        return _handle_source_rows(conn, query, authorized_cost_centre)
    # Unreachable: run_calculation() already validated intent against
    # SUPPORTED_INTENTS before calling _dispatch().
    raise EngineError("UNKNOWN_INTENT", f"Unsupported intent: {intent!r}")


# --------------------------------------------------------------------------
# Database retrieval helpers (DATABASE -> FILTER)
# --------------------------------------------------------------------------

def _fetch_expenses(
    conn: sqlite3.Connection,
    authorized_cost_centre: str,
    category: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve expense rows for the authorized cost centre, with optional
    filters, and convert them from sqlite3.Row to plain dict (required by
    calculation/formulas.py). Date range is inclusive on both ends.
    """
    sql = "SELECT * FROM expenses WHERE cost_centre = ?"
    params: List[Any] = [authorized_cost_centre]

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
    authorized_cost_centre: str,
    category: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
) -> Dict[str, Any]:
    """
    Locate the single applicable budget row for the authorized cost centre.

    `category` is REQUIRED: budgets are stored per (cost_centre, category),
    so a budget cannot be identified without one.

    If date_start/date_end are supplied, they must match the budget row's
    period_start/period_end EXACTLY. INTEGRATION_CONTRACT.md does not define
    overlapping/partial-period budget semantics, so engine.py does not guess
    at that -- the caller must name the exact period it wants. If they are
    omitted, exactly one budget row must exist for the cost_centre/category
    pair, or the lookup is ambiguous.

    Never invents a budget. Raises EngineError on any failure to find
    exactly one matching row.
    """
    if not category:
        raise EngineError(
            "MISSING_CATEGORY",
            "A 'category' is required to identify the applicable budget.",
        )

    sql = "SELECT * FROM budgets WHERE cost_centre = ? AND category = ?"
    params: List[Any] = [authorized_cost_centre, category]
    if date_start is not None:
        sql += " AND period_start = ?"
        params.append(date_start)
    if date_end is not None:
        sql += " AND period_end = ?"
        params.append(date_end)

    rows = conn.execute(sql, params).fetchall()
    budgets = [dict(row) for row in rows]

    if not budgets:
        period_note = f", period {date_start} to {date_end}" if (date_start or date_end) else " (no period specified)"
        raise EngineError(
            "BUDGET_NOT_FOUND",
            f"No budget found for cost_centre={authorized_cost_centre!r}, "
            f"category={category!r}{period_note}.",
        )
    if len(budgets) > 1:
        raise EngineError(
            "AMBIGUOUS_BUDGET",
            f"{len(budgets)} budgets match cost_centre={authorized_cost_centre!r}, "
            f"category={category!r}; specify date_start/date_end to select exactly one period.",
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
      currencies into a single number would be misleading, since this
      engine performs no conversion. Raises EngineError if more than one
      currency is present.
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
            "supply an engine-level 'currency' filter to get a meaningful result.",
        )
    if len(currencies) == 1:
        return next(iter(currencies))
    return None


# --------------------------------------------------------------------------
# Shared result builders
# --------------------------------------------------------------------------

def _build_filters(
    authorized_cost_centre: str,
    category: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    currency: Optional[str] = None,
    top_n: Optional[int] = None,
) -> Dict[str, Any]:
    """Build a human-readable record of which filters were actually applied."""
    filters: Dict[str, Any] = {"cost_centre": authorized_cost_centre}
    if category is not None:
        filters["category"] = category
    if date_start is not None or date_end is not None:
        filters["date_range"] = f"{date_start or '...'} to {date_end or '...'}"
    if currency is not None:
        filters["currency"] = currency
    if top_n is not None:
        filters["top_n"] = top_n
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
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")  # engine-level field, not in the contract

    expenses = _fetch_expenses(conn, authorized_cost_centre, category, date_start, date_end, currency)

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
        filters=_build_filters(authorized_cost_centre, category, date_start, date_end, currency),
        row_count=len(expenses),
    )


def _handle_category_spending(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")

    expenses = _fetch_expenses(conn, authorized_cost_centre, category, date_start, date_end, currency)

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
        filters=_build_filters(authorized_cost_centre, category, date_start, date_end, currency),
        row_count=len(expenses),
    )


def _handle_expense_count(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")

    expenses = _fetch_expenses(conn, authorized_cost_centre, category, date_start, date_end, currency)
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
        filters=_build_filters(authorized_cost_centre, category, date_start, date_end, currency),
        row_count=count,
    )


def _handle_top_transactions(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")
    top_n = query.get("top_n", 5)  # engine-level field; formulas.py validates it

    expenses = _fetch_expenses(conn, authorized_cost_centre, category, date_start, date_end, currency)

    # Validate currency compatibility BEFORE ranking. "Top N by amount"
    # across mixed currencies would rank a USD figure against an INR figure
    # as if they were the same unit -- that is exactly the kind of
    # misleading combination this engine must not produce silently, so the
    # check runs over the full candidate set, before calling
    # calculate_top_transactions(), not just over whichever records happen
    # to end up in the top N.
    resolved_currency = _resolve_currency(expenses, currency)
    top_records = calculate_top_transactions(expenses, top_n)  # sorting done by formulas.py
    source_rows = [r["expense_id"] for r in top_records]

    return _success(
        result=top_records,  # full records preserved -- no evidence lost
        source_rows=source_rows,
        currency=resolved_currency,
        formula=f"TOP {top_n} BY amount DESC",
        filters=_build_filters(authorized_cost_centre, category, date_start, date_end, currency, top_n),
        row_count=len(expenses),
    )


def _handle_remaining_budget(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")

    # Never invents a budget -- raises BUDGET_NOT_FOUND / AMBIGUOUS_BUDGET
    # via EngineError, caught by run_calculation().
    budget = _fetch_budget(conn, authorized_cost_centre, category, date_start, date_end)

    # "Remaining budget" means what's left of THIS budget's own period, so
    # spend is measured over budget["period_start"]..budget["period_end"],
    # not any caller-supplied range (which was only used to pick the budget).
    expenses = _fetch_expenses(
        conn,
        authorized_cost_centre,
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
            authorized_cost_centre, category, budget["period_start"], budget["period_end"], currency
        ),
        row_count=len(expenses),
        budget_id=budget["budget_id"],
        budget_amount=budget["amount"],
        spend=spend,
    )


def _handle_burn_rate(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    category = query.get("category")
    date_start = query.get("date_start")
    date_end = query.get("date_end")
    currency = query.get("currency")

    budget = _fetch_budget(conn, authorized_cost_centre, category, date_start, date_end)

    expenses = _fetch_expenses(
        conn,
        authorized_cost_centre,
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
            authorized_cost_centre, category, budget["period_start"], budget["period_end"], currency
        ),
        row_count=len(expenses),
        budget_id=budget["budget_id"],
        budget_amount=budget["amount"],
        spend=spend,
    )


def _handle_source_rows(
    conn: sqlite3.Connection, query: Mapping[str, Any], authorized_cost_centre: str
) -> Dict[str, Any]:
    """
    Engine-level source-row lookup/retrieval (operation 7 from the task
    requirements). NOT part of INTEGRATION_CONTRACT.md's documented query
    fields -- reads an engine-level 'expense_ids' list so the audit/
    evidence layer can re-fetch full records behind a previously returned
    source_rows list. Every row is still constrained to
    authorized_cost_centre; an id belonging to a different cost centre is
    simply excluded from the result, never leaked.

    If an engine-level 'currency' is supplied, it is applied as a real SQL
    filter (parameterized, never string-interpolated) -- only matching
    rows are returned, and "currency" in the result reflects what was
    actually fetched, not merely what was requested. If no currency is
    supplied, all matching rows are returned and the existing
    mixed-currency detection (_resolve_currency) still applies: a result
    spanning more than one currency is refused rather than silently mixed.
    """
    expense_ids = query.get("expense_ids")
    if not expense_ids or not isinstance(expense_ids, (list, tuple)):
        raise EngineError(
            "MISSING_EXPENSE_IDS",
            "'expense_ids' (a non-empty list of expense_id strings) is required for the source_rows intent.",
        )

    currency = query.get("currency")
    placeholders = ",".join("?" for _ in expense_ids)
    sql = f"SELECT * FROM expenses WHERE cost_centre = ? AND expense_id IN ({placeholders})"
    params: List[Any] = [authorized_cost_centre, *expense_ids]

    # BUG FIX: an explicit currency filter must actually constrain the SQL,
    # not just be echoed back afterward -- otherwise a caller could request
    # currency="INR" and silently receive USD rows mixed in. Parameterized
    # just like every other filter here; never string-interpolated.
    if currency is not None:
        sql += " AND currency = ?"
        params.append(currency)

    rows = conn.execute(sql, params).fetchall()
    records = [dict(row) for row in rows]

    # If no currency was supplied, preserve the existing mixed-currency
    # detection: reject rather than silently mix INR/USD/EUR records.
    resolved_currency = _resolve_currency(records, currency)
    source_rows = [r["expense_id"] for r in records]

    return _success(
        result=records,
        source_rows=source_rows,
        currency=resolved_currency,
        formula="SELECT * WHERE expense_id IN (...)",
        filters=_build_filters(authorized_cost_centre, currency=currency),
        row_count=len(records),
    )
