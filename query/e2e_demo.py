"""Manual Query Compiler demo.

This file intentionally is not named *_test.py so pytest does not auto-discover it.
It demonstrates the public compiler contract without implementing database or
calculation-engine logic.
"""

from datetime import date

from .compiler import compile_query
from .schema import AuthorizationScope, ScopeType


def run_demo(prompt: str, scope: AuthorizationScope) -> None:
    print("=" * 70)
    print(f"Prompt: {prompt}")
    print(f"Trusted scope: {scope.model_dump()}")

    response = compile_query(
        prompt,
        scope=scope,
        current_date=date(2026, 10, 4),
    )

    print(f"Status: {response.status}")

    if response.query is not None:
        print("Structured query:")
        print(response.query.model_dump())
    else:
        print(f"Message: {response.message}")

    print()


if __name__ == "__main__":
    manager_scope = AuthorizationScope(
        user_id="U-002",
        role="Manager",
        scope_type=ScopeType.cost_centre,
        cost_centre="CC-TECH",
    )

    employee_scope = AuthorizationScope(
        user_id="U-001",
        role="Employee",
        scope_type=ScopeType.user,
        scope_user_id="U-001",
    )

    admin_scope = AuthorizationScope(
        user_id="U-003",
        role="Admin",
        scope_type=ScopeType.organization,
    )

    run_demo("How much did I spend on food this month?", manager_scope)
    run_demo("Show my top 3 travel expenses this month.", manager_scope)
    run_demo("How much did I spend in Q1 2025?", employee_scope)
    run_demo("What's the weather today?", admin_scope)
    run_demo("How much did I spend on entertainment this month?", employee_scope)
