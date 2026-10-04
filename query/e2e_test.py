import pandas as pd
from pathlib import Path

from compiler import compile_query, Status, Intent
from schema import AuthorizationScope, ScopeType


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(r"C:\Users\niket\OneDrive\Desktop\hexa nova hackthon")

EXPENSES_FILE = BASE_DIR / "sample_expenses.csv"
BUDGETS_FILE = BASE_DIR / "sample_budgets.csv"
USERS_FILE = BASE_DIR / "sample_users.csv"


# ============================================================
# LOAD CSV FILES
# ============================================================

if not EXPENSES_FILE.exists():
    raise FileNotFoundError(f"Expenses file not found:\n{EXPENSES_FILE}")

if not BUDGETS_FILE.exists():
    raise FileNotFoundError(f"Budgets file not found:\n{BUDGETS_FILE}")

if not USERS_FILE.exists():
    raise FileNotFoundError(f"Users file not found:\n{USERS_FILE}")


expenses = pd.read_csv(
    EXPENSES_FILE,
    parse_dates=["date"]
)

budgets = pd.read_csv(
    BUDGETS_FILE,
    parse_dates=["period_start", "period_end"]
)

users = pd.read_csv(USERS_FILE)


# ============================================================
# DATA CLEANING
# ============================================================

expenses["date"] = pd.to_datetime(
    expenses["date"],
    errors="coerce"
)

budgets["period_start"] = pd.to_datetime(
    budgets["period_start"],
    errors="coerce"
)

budgets["period_end"] = pd.to_datetime(
    budgets["period_end"],
    errors="coerce"
)

expenses["amount"] = pd.to_numeric(
    expenses["amount"],
    errors="coerce"
)

budgets["amount"] = pd.to_numeric(
    budgets["amount"],
    errors="coerce"
)


# ============================================================
# DISPLAY LOADED DATA
# ============================================================

print()
print("=" * 60)
print("CSV FILES LOADED")
print("=" * 60)

print("\nExpenses:")
print(expenses.head())

print("\nBudgets:")
print(budgets.head())

print("\nUsers:")
print(users.head())

print()
print("=" * 60)
print("DATA INFORMATION")
print("=" * 60)

print(f"\nNumber of expenses: {len(expenses)}")
print(f"Number of budgets: {len(budgets)}")
print(f"Number of users: {len(users)}")


# ============================================================
# HELPER: FILTER EXPENSES
# ============================================================

def filter_expenses(query):
    filtered = expenses.copy()

    # --------------------------------------------------------
    # USER / COST CENTRE SECURITY FILTER
    # --------------------------------------------------------

    filtered = filtered[
        filtered["cost_centre"].astype(str).str.upper()
        == query.scope.cost_centre.upper()
    ]

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    if query.category:
        filtered = filtered[
            filtered["category"].astype(str).str.lower()
            == query.category.lower()
        ]

    # --------------------------------------------------------
    # DATE FILTER
    # --------------------------------------------------------

    if query.date_range_start:
        start_date = pd.Timestamp(query.date_range_start)

        filtered = filtered[
            filtered["date"] >= start_date
        ]

    if query.date_range_end:
        end_date = pd.Timestamp(query.date_range_end)

        filtered = filtered[
            filtered["date"] <= end_date
        ]

    return filtered


# ============================================================
# RUN QUERY
# ============================================================

def run_query(prompt):
    print()
    print("=" * 70)
    print(f"Prompt: {prompt}")

    # --------------------------------------------------------
    # STEP 1: COMPILE NATURAL LANGUAGE QUERY
    # --------------------------------------------------------

    response = compile_query(
        prompt,
        scope=AuthorizationScope(user_id="U-002", role="Manager", scope_type=ScopeType.cost_centre, cost_centre="CC-TECH")
    )

    print(f"Status: {response.status}")

    # --------------------------------------------------------
    # STEP 2: HANDLE CLARIFY / REFUSED
    # --------------------------------------------------------

    if response.status != Status.SUCCESS:
        print(f"Message: {response.message}")
        return

    query = response.query

    print("Compiled Query:")
    print(query)

    # --------------------------------------------------------
    # STEP 3: FILTER EXPENSE DATA
    # --------------------------------------------------------

    filtered = filter_expenses(query)

    # ========================================================
    # SUM EXPENSES
    # ========================================================

    if query.intent == Intent.sum_expenses:

        total = filtered["amount"].sum()

        print()
        print("Result:")
        print(f"Total spent: ₹{total:,.2f}")
        print(f"Transaction count: {len(filtered)}")

        if query.date_range_start and query.date_range_end:
            print(
                f"Date range: "
                f"{query.date_range_start} to "
                f"{query.date_range_end}"
            )

        if query.category:
            print(f"Category: {query.category}")

        print(f"Scope: {query.scope.model_dump()}")

        print()
        print("Source rows:")

        if filtered.empty:
            print("No matching transactions found.")
        else:
            print(
                filtered[
                    [
                        "expense_id",
                        "category",
                        "amount",
                        "currency",
                        "date",
                        "description"
                    ]
                ].to_string(index=False)
            )

    # ========================================================
    # COUNT EXPENSES
    # ========================================================

    elif query.intent == Intent.count_expenses:

        count = len(filtered)

        print()
        print("Result:")
        print(f"Number of expenses: {count}")

        print()
        print("Source rows:")

        if filtered.empty:
            print("No matching transactions found.")
        else:
            print(
                filtered[
                    [
                        "expense_id",
                        "category",
                        "amount",
                        "date",
                        "description"
                    ]
                ].to_string(index=False)
            )

    # ========================================================
    # TOP TRANSACTIONS
    # ========================================================

    elif query.intent == Intent.top_transactions:

        limit = query.limit or 3

        top_transactions = (
            filtered
            .sort_values(
                by="amount",
                ascending=False
            )
            .head(limit)
        )

        print()
        print("Result:")
        print(f"Top {limit} transactions:")

        if top_transactions.empty:
            print("No matching transactions found.")
        else:
            print(
                top_transactions[
                    [
                        "expense_id",
                        "category",
                        "amount",
                        "currency",
                        "date",
                        "description"
                    ]
                ].to_string(index=False)
            )

    # ========================================================
    # CATEGORY BREAKDOWN
    # ========================================================

    elif query.intent == Intent.category_breakdown:

        breakdown = (
            filtered
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        print()
        print("Result:")
        print("Category breakdown:")

        if breakdown.empty:
            print("No matching transactions found.")
        else:
            for category, amount in breakdown.items():
                print(
                    f"{category}: ₹{amount:,.2f}"
                )

    # ========================================================
    # SOURCE LOOKUP
    # ========================================================

    elif query.intent == Intent.source_lookup:

        print()
        print("Result:")
        print("Matching source transactions:")

        if filtered.empty:
            print("No matching transactions found.")
        else:
            print(
                filtered[
                    [
                        "expense_id",
                        "user_id",
                        "cost_centre",
                        "category",
                        "amount",
                        "currency",
                        "date",
                        "description"
                    ]
                ].to_string(index=False)
            )

    # ========================================================
    # REMAINING BUDGET
    # ========================================================

    elif query.intent == Intent.remaining_budget:

        budget_data = budgets.copy()

        # ----------------------------------------------------
        # Cost centre filter
        # ----------------------------------------------------

        budget_data = budget_data[
            budget_data["cost_centre"].astype(str).str.upper()
            == query.scope.cost_centre.upper()
        ]

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if query.category:
            budget_data = budget_data[
                budget_data["category"].astype(str).str.lower()
                == query.category.lower()
            ]

        # ----------------------------------------------------
        # Use current date when no explicit period is given
        # ----------------------------------------------------

        today = pd.Timestamp.today().normalize()

        current_budget = budget_data[
            (budget_data["period_start"] <= today)
            & (budget_data["period_end"] >= today)
        ]

        # If there is no budget covering today,
        # use all matching budget records.
        if current_budget.empty:
            current_budget = budget_data

        budget_amount = current_budget["amount"].sum()

        # ----------------------------------------------------
        # Calculate actual spending
        # ----------------------------------------------------

        actual_expenses = expenses.copy()

        actual_expenses = actual_expenses[
            actual_expenses["cost_centre"].astype(str).str.upper()
            == query.scope.cost_centre.upper()
        ]

        if query.category:
            actual_expenses = actual_expenses[
                actual_expenses["category"].astype(str).str.lower()
                == query.category.lower()
            ]

        if not current_budget.empty:

            period_start = current_budget["period_start"].min()
            period_end = current_budget["period_end"].max()

            actual_expenses = actual_expenses[
                (actual_expenses["date"] >= period_start)
                & (actual_expenses["date"] <= period_end)
            ]

        actual_spending = actual_expenses["amount"].sum()

        remaining = budget_amount - actual_spending

        print()
        print("Result:")
        print(f"Budget: ₹{budget_amount:,.2f}")
        print(f"Actual spending: ₹{actual_spending:,.2f}")
        print(f"Remaining budget: ₹{remaining:,.2f}")

        print()
        print("Formula:")
        print(
            f"Remaining = Budget - Actual Spending"
        )
        print(
            f"Remaining = ₹{budget_amount:,.2f} "
            f"- ₹{actual_spending:,.2f}"
        )
        print(
            f"Remaining = ₹{remaining:,.2f}"
        )

    # ========================================================
    # UNKNOWN INTENT
    # ========================================================

    else:

        print()
        print("This intent is not implemented yet.")


# ============================================================
# QUERY COMPILER TEST
# ============================================================

print()
print("=" * 60)
print("QUERY COMPILER TEST")
print("=" * 60)


compiler_tests = [
    "How much did I spend on food this month?",
    "What were my expenses in August 2026?",
    "How much did I spend on travel this month?",
    "Show my top 3 travel expenses this month.",
    "How many food expenses did I submit this month?",
    "How much did I spend in Q1 2025?",
    "How much did I spend in 2025?",
    "How much budget is left for Travel?",
]


for prompt in compiler_tests:

    response = compile_query(
        prompt,
        scope=AuthorizationScope(user_id="U-002", role="Manager", scope_type=ScopeType.cost_centre, cost_centre="CC-TECH")
    )

    print()
    print("-" * 70)
    print(f"Prompt: {prompt}")
    print(f"Status: {response.status}")

    if response.query:
        print("Query:")
        print(response.query)

    if response.message:
        print(f"Message: {response.message}")


# ============================================================
# REAL END-TO-END TEST
# ============================================================

print()
print("=" * 60)
print("REAL END-TO-END TEST")
print("=" * 60)


run_query(
    "How much did I spend on Food this month?"
)

run_query(
    "How much did I spend on Travel this month?"
)

run_query(
    "Show my top 3 Travel expenses this month."
)

run_query(
    "How many Food expenses did I submit this month?"
)

run_query(
    "What were my expenses in August 2026?"
)

run_query(
    "How much did I spend in Q1 2025?"
)

run_query(
    "How much budget is left for Travel?"
)