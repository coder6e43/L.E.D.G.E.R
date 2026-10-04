"""
compiler.py — Query Compiler module (Niketan)
Converts a natural-language financial question into a validated,
structured Query object (schema.py), or a CLARIFY / REFUSED response.
Pure rule-based parsing (keyword matching + date resolution) — no LLM
required for the MVP. Deterministic and easy to debug, matching the
project's "no guessing" architecture.
Usage:
    from compiler import compile_query
    result = compile_query("How much did I spend on food this month?",
                            user_scope="CC-TECH")
"""
import re
import calendar
from datetime import date, timedelta
from typing import List, Optional, Tuple
from dateutil.relativedelta import relativedelta
from pydantic import ValidationError
from .schema import (
    Query, CompilerResponse, Status, Intent,
    normalize_category, mentions_unknown_category, CANONICAL_CATEGORIES,
)
# =======================================================================
# Intent detection
# =======================================================================
def detect_intent(text: str) -> Optional[Intent]:
    """Pure keyword matching. Order matters — most specific phrasing first."""
    text_lower = text.lower()
    if any(k in text_lower for k in ["remaining", "left", "budget left", "how much budget"]):
        return Intent.remaining_budget
    if any(k in text_lower for k in ["top", "biggest", "largest", "highest", "outlier"]):
        return Intent.top_transactions
    if any(k in text_lower for k in ["how many", "number of", "count of"]):
        return Intent.count_expenses
    if any(k in text_lower for k in ["breakdown", "by category", "split by", "distribution"]):
        return Intent.category_breakdown
    if any(k in text_lower for k in [
        "show transactions", "show me the transactions", "source rows",
        "which transactions", "list transactions", "included in that","my transactions",
    "travel transactions",
    ]):
        return Intent.source_lookup
    if any(k in text_lower for k in [
        "how much", "total", "spend", "spent", "spending", "expense", "expenses",
    ]):
        return Intent.sum_expenses
    return None  # Unrecognized — caller should trigger a safe refusal
# =======================================================================
# Safe refusal checks
# =======================================================================
# Note: cross-user/cross-cost-centre access control is NOT handled here —
# that is enforced server-side by the Authentication/RBAC module.
FUTURE_KEYWORDS = [
    "will spend", "next year", "next quarter", "next month",
    "forecast", "predict", "projection", "going to spend",
]
OUT_OF_DOMAIN_HINTS = [
    "weather", "who is the ceo", "capital of", "joke", "recipe",
]
def is_future_prediction(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in FUTURE_KEYWORDS)
def is_out_of_domain(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in OUT_OF_DOMAIN_HINTS)
# =======================================================================
# Date resolution
# =======================================================================
MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}
def _month_bounds(year: int, month: int) -> Tuple[date, date]:
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)
    return start, end
def _quarter_bounds(year: int, quarter: int) -> Tuple[date, date]:
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end = _month_bounds(year, start_month + 2)[1]
    return start, end
def _week_bounds(any_day_in_week: date) -> Tuple[date, date]:
    """Monday-to-Sunday calendar week containing any_day_in_week."""
    monday = any_day_in_week - timedelta(days=any_day_in_week.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday
# --- Explicit full-date patterns (day-level precision), checked first ---
# These take priority over relative phrases because they're unambiguous.
_DAY_MONTH_YEAR_RE = re.compile(
    r"\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|"
    r"september|october|november|december)(?:\s+(\d{4}))?\b"
)
_SLASH_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")  # DD/MM/YYYY
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
def _extract_explicit_dates(text_lower: str, current_date: date) -> List[date]:
    """Find every concrete calendar date mentioned, in any supported
    format, so phrases like 'from 1 September to 20 September' or
    'between 2026-09-01 and 2026-09-20' both resolve the same way:
    collect every date found, then the caller takes min/max as a range.
    If a 'day + month' mention has no year attached (e.g. the first half
    of 'from 1 September to 20 September 2026'), the current year is
    assumed — the same default used for bare month names."""
    found: List[date] = []
    for m in _DAY_MONTH_YEAR_RE.finditer(text_lower):
        day, month_name, year = m.group(1), m.group(2), m.group(3)
        year_val = int(year) if year else current_date.year
        try:
            found.append(date(year_val, MONTH_NAMES[month_name], int(day)))
        except ValueError:
            pass  # not a real calendar date — ignore rather than crash
    for m in _SLASH_DATE_RE.finditer(text_lower):
        day, month, year = m.groups()
        try:
            found.append(date(int(year), int(month), int(day)))
        except ValueError:
            pass  # not a real calendar date — ignore rather than crash
    for m in _ISO_DATE_RE.finditer(text_lower):
        year, month, day = m.groups()
        try:
            found.append(date(int(year), int(month), int(day)))
        except ValueError:
            pass
    return found
def resolve_date_range(
    text: str, current_date: Optional[date] = None
) -> Tuple[Optional[date], Optional[date]]:
    """
    Returns (start_date, end_date), or (None, None) if nothing recognized.
    """
    if current_date is None:
        current_date = date.today()
    text_lower = text.lower()
    # ---------------------------------------------------------------
    # 1. Explicit day-level dates
    # ---------------------------------------------------------------
    explicit_dates = _extract_explicit_dates(
        text_lower,
        current_date
    )
    if len(explicit_dates) >= 2:
        return min(explicit_dates), max(explicit_dates)
    if len(explicit_dates) == 1:
        return explicit_dates[0], explicit_dates[0]
    # ---------------------------------------------------------------
    # 2. Month + year
    # Example: August 2026
    # ---------------------------------------------------------------
    for month_name, month_num in MONTH_NAMES.items():
        match = re.search(
            rf"\b{month_name}\s+(\d{{4}})\b",
            text_lower
        )
        if match:
            year = int(match.group(1))
            return _month_bounds(year, month_num)
    # ---------------------------------------------------------------
    # 3. Yesterday
    # ---------------------------------------------------------------
    if re.search(r"\byesterday\b", text_lower):
        yesterday = current_date - timedelta(days=1)
        return yesterday, yesterday
    # ---------------------------------------------------------------
    # 4. Today
    # ---------------------------------------------------------------
    if re.search(r"\btoday\b", text_lower):
        return current_date, current_date
    # ---------------------------------------------------------------
    # 5. This week
    # ---------------------------------------------------------------
    if re.search(r"\bthis week\b", text_lower):
        monday, _ = _week_bounds(current_date)
        return monday, current_date
    # ---------------------------------------------------------------
    # 6. Last week
    # ---------------------------------------------------------------
    if re.search(r"\blast week\b", text_lower):
        this_monday, _ = _week_bounds(current_date)
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(days=1)
        return last_monday, last_sunday
    # ---------------------------------------------------------------
    # 7. This month
    # ---------------------------------------------------------------
    if re.search(r"\bthis month\b", text_lower):
        start, _ = _month_bounds(
            current_date.year,
            current_date.month
        )
        return start, current_date
    # ---------------------------------------------------------------
    # 8. Last month
    # ---------------------------------------------------------------
    if re.search(r"\blast month\b", text_lower):
        first_of_this_month = current_date.replace(day=1)
        last_month_date = (
            first_of_this_month -
            relativedelta(months=1)
        )
        return _month_bounds(
            last_month_date.year,
            last_month_date.month
        )
    # ---------------------------------------------------------------
    # 9. Specific quarter
    # IMPORTANT: Check Q1 2025 BEFORE generic "this quarter"
    #
    # Examples:
    # Q1 2025
    # Q2 2026
    # Q3
    # ---------------------------------------------------------------
    quarter_match = re.search(
        r"\bq([1-4])(?:\s+(\d{4}))?\b",
        text_lower
    )
    if quarter_match:
        quarter = int(quarter_match.group(1))
        if quarter_match.group(2):
            year = int(quarter_match.group(2))
        else:
            year = current_date.year
        return _quarter_bounds(year, quarter)
    # ---------------------------------------------------------------
    # 10. Last quarter
    # ---------------------------------------------------------------
    if re.search(r"\blast quarter\b", text_lower):
        current_quarter = (
            (current_date.month - 1) // 3 + 1
        )
        if current_quarter == 1:
            return _quarter_bounds(
                current_date.year - 1,
                4
            )
        return _quarter_bounds(
            current_date.year,
            current_quarter - 1
        )
    # ---------------------------------------------------------------
    # 11. This quarter
    # ---------------------------------------------------------------
    if re.search(r"\bthis quarter\b", text_lower):
        current_quarter = (
            (current_date.month - 1) // 3 + 1
        )
        start, _ = _quarter_bounds(
            current_date.year,
            current_quarter
        )
        return start, current_date
    # ---------------------------------------------------------------
    # 12. Year to date
    # ---------------------------------------------------------------
    if (
        re.search(r"\byear to date\b", text_lower)
        or re.search(r"\bytd\b", text_lower)
    ):
        return date(
            current_date.year,
            1,
            1
        ), current_date
     # ---------------------------------------------------------------
    # 13. Full year
    # Example: "How much did I spend in 2025?"
    # Requires a preceding context word (in/for/during) so a stray
    # 4-digit number elsewhere in the sentence (e.g. an invoice number)
    # isn't mistaken for a year reference.
    # ---------------------------------------------------------------
    year_match = re.search(
        r"\b(?:in|for|during)\s+(20\d{2})\b",
        text_lower
    )
    if year_match:
        year = int(year_match.group(1))
        return date(year, 1, 1), date(year, 12, 31)
    # ---------------------------------------------------------------
    # 14. Bare month name
    # Example: September
    # ---------------------------------------------------------------
    for month_name, month_num in MONTH_NAMES.items():
        if re.search(
            rf"\b{month_name}\b",
            text_lower
        ):
            return _month_bounds(
                current_date.year,
                month_num
            )
    # ---------------------------------------------------------------
    # 15. Nothing recognized
    # ---------------------------------------------------------------
    return None, None
# =======================================================================
# Main entry point
# =======================================================================
DATE_REQUIRED_INTENTS = {
    Intent.sum_expenses,
    Intent.category_breakdown,
    Intent.top_transactions,
    Intent.count_expenses,
}
def compile_query(
    prompt: str, user_scope: str, current_date: Optional[date] = None
) -> CompilerResponse:
    """
    prompt:        raw natural-language question from the user
    user_scope:    the AUTHENTICATED cost-centre/user scope from the session
                   (never taken from the prompt itself — see Auth module)
    current_date:  inject "today" for deterministic testing; defaults to
                   the real today if omitted
    """
    if current_date is None:
        current_date = date.today()
    # --- Step 1: Refusal checks that don't need anything else ---
    if is_future_prediction(prompt):
        return CompilerResponse(
            status=Status.REFUSED,
            message="Cannot compute future spending from historical expense records.",
        )
    if is_out_of_domain(prompt):
        return CompilerResponse(
            status=Status.REFUSED,
            message="I can only answer questions related to your authorized expense and budget records.",
        )
    # --- Step 2: Detect intent ---
    intent = detect_intent(prompt)
    if intent is None:
        return CompilerResponse(
            status=Status.REFUSED,
            message="I couldn't match this question to a supported financial query type.",
        )
    # --- Step 3: Detect category ---
    category = normalize_category(prompt)
    if mentions_unknown_category(prompt):
        return CompilerResponse(
            status=Status.CLARIFY,
            message=(
                "I cannot identify that category in our corporate taxonomy. "
                f"Available categories: {', '.join(CANONICAL_CATEGORIES)}."
            ),
        )
    if intent == Intent.remaining_budget and category is None:
        return CompilerResponse(
            status=Status.CLARIFY,
            message="Please specify which category's budget you're asking about (e.g. Travel, Food).",
        )
    # --- Step 4: Resolve dates ---
    date_start, date_end = resolve_date_range(prompt, current_date)
    if intent in DATE_REQUIRED_INTENTS and date_start is None:
        return CompilerResponse(
            status=Status.CLARIFY,
            message="Please clarify your requested time period (e.g. 'this month', 'last month', 'August 2026').",
        )
    # --- Step 5: Extract a limit for top_transactions (default 3) ---
    limit = None
    if intent == Intent.top_transactions:
        match = re.search(r"\b(\d+)\b", prompt)
        limit = int(match.group(1)) if match else 3
    # --- Step 6: Build and validate the structured query ---
    try:
        query = Query(
            intent=intent,
            user_scope=user_scope,
            category=category,
            date_range_start=date_start,
            date_range_end=date_end,
            limit=limit,
        )
    except ValidationError as e:
        return CompilerResponse(status=Status.REFUSED, message=f"Invalid query: {e}")
    return CompilerResponse(status=Status.SUCCESS, query=query)
# =======================================================================
# Quick manual smoke test — run this file directly: python compiler.py
# =======================================================================
if __name__ == "__main__":
    TODAY = date(2026, 9, 20)
    test_cases = [
    "How much did I spend on food this month?",
    "What were my expenses in August 2026?",
    "Show my dining and lunch spending this month.",
    "How much travel budget do I have left?",
    "Show transactions in that travel total.",
    "How much did I spend?",
    "How much will I spend on travel next year?",
    "What's the weather today?",
    "Show my top 3 travel expenses this month.",
    "How many food expenses did I submit this month?",
    "How much did I spend in Q1 2025?",
    "How much did I spend in 2025?",
        "How much did I spend on Utilities?",
    "How much Marketing budget is left?",
    "Show my Software expenses.",
    "How much did I spend on Snacks?",
    "How much Food spending was there?",
    "Show my Travel expenses.",
    "How much did I spend on Office Supplies?",
    "How many Training expenses are there?",
    "Show my top 3 Marketing expenses.",
    "How much budget is left for Utilities?",
    "How much did I spend on Miscellaneous expenses?",
    "Show my Travel transactions.",
    "How much did I spend on electricity?",
    "How much did I spend on printer cartridges?",
    "How much did I spend on fuel reimbursement?",
    ]
    for prompt in test_cases:
        result = compile_query(prompt, user_scope="CC-TECH", current_date=TODAY)
        print(f"\nPrompt:  {prompt}")
        print(f"Status:  {result.status}")
        if result.query:
            print(f"Query:   {result.query.model_dump()}")
        if result.message:
            print(f"Message: {result.message}")