import math
from typing import Any, Dict, Iterable, List, Mapping

Expense = Mapping[str, Any]


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _validate_number(value: Any, label: str) -> float:
    """Return value as a float, or raise a clear error if it is unusable."""
    # bool is a subclass of int, but True/False is never a valid money amount.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a number, got {type(value).__name__}: {value!r}")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{label} must be a finite number, got {value!r}")
    return float(value)


def _get_amount(expense: Expense) -> float:
    """Read and validate the 'amount' field of one expense record."""
    expense_id = expense.get("expense_id", "<unknown>")
    if "amount" not in expense or expense["amount"] is None:
        raise ValueError(f"Expense {expense_id} is missing 'amount'")
    return _validate_number(expense["amount"], f"amount of expense {expense_id}")


# --------------------------------------------------------------------------
# A) Total expenses
# --------------------------------------------------------------------------

def calculate_total_expenses(expenses: Iterable[Expense]) -> float:
    """
    Sum of the 'amount' field over all given expenses: SUM(amount).

    Input:  iterable of expense dicts.
    Output: float total. An empty input returns 0.0 (a real, correct total).
    Raises: ValueError / TypeError if any amount is missing or unusable.

    Example: amounts [1000, 2000, 500] -> 3500.0
    """
    return math.fsum(_get_amount(expense) for expense in expenses)


# --------------------------------------------------------------------------
# B) Category-wise spending
# --------------------------------------------------------------------------

def calculate_category_spending(expenses: Iterable[Expense]) -> Dict[str, float]:
    """
    Total spending per category.

    Input:  iterable of expense dicts (needs 'category' and 'amount').
    Output: {category: total}, in order of first appearance.
            Empty input returns {}.
    Raises: ValueError if a record has no category; amount errors as above.

    Example: Food 1000, Food 2000, Travel 500 -> {"Food": 3000.0, "Travel": 500.0}
    """
    amounts_by_category: Dict[str, List[float]] = {}
    for expense in expenses:
        category = expense.get("category")
        if category is None:
            expense_id = expense.get("expense_id", "<unknown>")
            raise ValueError(f"Expense {expense_id} is missing 'category'")
        amounts_by_category.setdefault(category, []).append(_get_amount(expense))

    return {category: math.fsum(amounts) for category, amounts in amounts_by_category.items()}


# --------------------------------------------------------------------------
# C) Expense count
# --------------------------------------------------------------------------

def calculate_expense_count(expenses: Iterable[Expense]) -> int:
    """
    Number of expense records.

    Input:  iterable of expense dicts.
    Output: int (0 for empty input). Amounts are not inspected: this counts rows.
    """
    return sum(1 for _ in expenses)


# --------------------------------------------------------------------------
# D) Top transactions
# --------------------------------------------------------------------------

def calculate_top_transactions(expenses: Iterable[Expense], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    The top_n highest-amount expenses, highest first.

    Input:  iterable of expense dicts; top_n must be an int >= 1.
    Output: list of full record copies (expense_id and every other field is
            kept, so engine.py can use them as source-row evidence).
            If top_n exceeds the number of records, all records are returned.
            Empty input returns [].
    Ties on amount are broken by expense_id (ascending) so output is deterministic.
    Raises: ValueError if top_n <= 0, TypeError if top_n is not an int;
            amount errors as above.

    Example: amounts 500, 2000, 1000, 3000 with top_n=2 -> 3000, 2000
    """
    if isinstance(top_n, bool) or not isinstance(top_n, int):
        raise TypeError(f"top_n must be an int, got {type(top_n).__name__}")
    if top_n <= 0:
        raise ValueError(f"top_n must be at least 1, got {top_n}")

    records = [dict(expense) for expense in expenses]
    records.sort(key=lambda r: (-_get_amount(r), str(r.get("expense_id", ""))))
    return records[:top_n]


# --------------------------------------------------------------------------
# E) Remaining budget
# --------------------------------------------------------------------------

def calculate_remaining_budget(budget_amount: float, spend: float) -> float:
    """
    Remaining Budget = Budget Amount - Expense Spend.

    Input:  budget_amount and spend as numbers (spend usually comes from
            calculate_total_expenses).
    Output: float. The result is negative when spend exceeds the budget
            (overspend); it is NOT clamped to zero, so overspend stays visible.
    Raises: TypeError / ValueError for non-numeric, NaN or infinite inputs;
            ValueError if budget_amount is negative.

    Example: budget 10000, spend 3500 -> 6500.0
    """
    budget = _validate_number(budget_amount, "budget_amount")
    spent = _validate_number(spend, "spend")
    if budget < 0:
        raise ValueError(f"budget_amount cannot be negative, got {budget}")
    return budget - spent


# --------------------------------------------------------------------------
# F) Budget burn rate
# --------------------------------------------------------------------------

def calculate_burn_rate(spend: float, budget_amount: float) -> float:
    """
    Burn Rate (%) = (Expense Spend / Budget Amount) * 100.

    Input:  spend and budget_amount as numbers.
    Output: float percentage, unrounded. Can exceed 100.0 on overspend.

    Zero-budget behaviour (deterministic):
      - budget == 0 and spend == 0 -> returns 0.0
      - budget == 0 and spend != 0 -> raises ValueError (burn rate is undefined;
        we never return infinity or NaN)
    A negative budget also raises ValueError.

    Example: spend 3000, budget 10000 -> 30.0
    """
    spent = _validate_number(spend, "spend")
    budget = _validate_number(budget_amount, "budget_amount")

    if budget < 0:
        raise ValueError(f"budget_amount cannot be negative, got {budget}")
    if budget == 0:
        if spent == 0:
            return 0.0
        raise ValueError("Burn rate is undefined: budget_amount is 0 but spend is not 0")

    return (spent / budget) * 100
