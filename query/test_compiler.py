"""Core deterministic Query Compiler tests."""

from datetime import date

from query.compiler import compile_query
from query.schema import AuthorizationScope, ScopeType, Intent, Status


SCOPE = AuthorizationScope(
    user_id="U-002",
    role="Manager",
    scope_type=ScopeType.cost_centre,
    cost_centre="CC-TECH",
)


def compile(prompt):
    return compile_query(prompt, scope=SCOPE, current_date=date(2026, 10, 4))


def test_sum_category_and_current_month():
    result = compile("How much did I spend on food this month?")
    assert result.status == Status.SUCCESS
    assert result.query.intent == Intent.sum_expenses
    assert result.query.category == "Food"
    assert result.query.date_range_start == date(2026, 10, 1)
    assert result.query.date_range_end == date(2026, 10, 4)


def test_month_year_parsing():
    result = compile("What were my expenses in August 2026?")
    assert result.status == Status.SUCCESS
    assert result.query.date_range_start == date(2026, 8, 1)
    assert result.query.date_range_end == date(2026, 8, 31)


def test_quarter_and_full_year_parsing():
    q1 = compile("How much did I spend in Q1 2025?")
    assert q1.status == Status.SUCCESS
    assert q1.query.date_range_start == date(2025, 1, 1)
    assert q1.query.date_range_end == date(2025, 3, 31)

    year = compile("How much did I spend in 2025?")
    assert year.status == Status.SUCCESS
    assert year.query.date_range_start == date(2025, 1, 1)
    assert year.query.date_range_end == date(2025, 12, 31)


def test_top_transactions_limit():
    result = compile("Show my top 3 travel expenses this month.")
    assert result.status == Status.SUCCESS
    assert result.query.intent == Intent.top_transactions
    assert result.query.category == "Travel"
    assert result.query.limit == 3


def test_budget_query_requires_category():
    result = compile("How much budget is left this month?")
    assert result.status == Status.CLARIFY


def test_source_lookup():
    result = compile("Show my Travel transactions this month.")
    assert result.status == Status.SUCCESS
    assert result.query.intent == Intent.source_lookup
    assert result.query.category == "Travel"


def test_future_prediction_is_refused():
    result = compile("How much will I spend on travel next year?")
    assert result.status == Status.REFUSED


def test_out_of_domain_is_refused():
    result = compile("What's the weather today?")
    assert result.status == Status.REFUSED


def test_unknown_category_requests_clarification():
    result = compile("How much did I spend on entertainment this month?")
    assert result.status == Status.CLARIFY


def test_date_range_is_deterministic():
    result = compile(
        "Show expenses from 1 September to 20 September 2026."
    )
    assert result.status == Status.SUCCESS
    assert result.query.date_range_start == date(2026, 9, 1)
    assert result.query.date_range_end == date(2026, 9, 20)


def test_scope_is_preserved_without_reinterpretation():
    employee = AuthorizationScope(
        user_id="U-001",
        role="Employee",
        scope_type=ScopeType.user,
        scope_user_id="U-001",
    )
    admin = AuthorizationScope(
        user_id="U-003",
        role="Admin",
        scope_type=ScopeType.organization,
    )

    employee_result = compile_query(
        "How much did I spend this month?",
        scope=employee,
        current_date=date(2026, 10, 4),
    )
    admin_result = compile_query(
        "How much did I spend this month?",
        scope=admin,
        current_date=date(2026, 10, 4),
    )

    assert employee_result.query.scope == employee
    assert employee_result.query.scope.scope_type == ScopeType.user
    assert employee_result.query.scope.cost_centre is None

    assert admin_result.query.scope == admin
    assert admin_result.query.scope.scope_type == ScopeType.organization
    assert admin_result.query.scope.cost_centre is None
