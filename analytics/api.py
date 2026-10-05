"""Read-only analytics built from the same RBAC-scoped expense database."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from auth.rbac import AuthorizationError, get_authorized_scope, has_permission
from auth.session import get_current_user
from database.connection import get_connection

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _scope_filter(scope: dict[str, str]) -> tuple[str, list[str]]:
    scope_type = scope.get("scope_type")
    if scope_type == "user" and scope.get("scope_user_id"):
        return " AND user_id = ?", [scope["scope_user_id"]]
    if scope_type == "cost_centre" and scope.get("cost_centre"):
        return " AND cost_centre = ?", [scope["cost_centre"]]
    if scope_type == "organization":
        return "", []
    raise HTTPException(status_code=403, detail="A valid authorized scope is required.")


def _month_keys(today: date, count: int = 12) -> list[str]:
    months: list[str] = []
    year, month = today.year, today.month
    for _ in range(count):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))


@router.get("/overview")
def analytics_overview() -> dict:
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        scope = get_authorized_scope(user)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail="Analytics access denied.") from exc
    required_permission = "expense:view_own" if scope["scope_type"] == "user" else "trend:view_cost_centre"
    if not has_permission(user, required_permission):
        raise HTTPException(status_code=403, detail="Analytics access denied.")
    if scope["scope_type"] == "organization" and not has_permission(user, "cost_centre:view_all"):
        raise HTTPException(status_code=403, detail="Organization analytics access denied.")

    today = date.today()
    month_keys = _month_keys(today)
    start_year, start_month = map(int, month_keys[0].split("-"))
    start_date = f"{start_year:04d}-{start_month:02d}-01"
    end_date = today.isoformat()
    scope_sql, scope_params = _scope_filter(scope)

    with get_connection() as conn:
        currencies = [row["currency"] for row in conn.execute(
            f"SELECT DISTINCT currency FROM expenses WHERE date >= ? AND date <= ?{scope_sql} ORDER BY currency",
            (start_date, end_date, *scope_params),
        ).fetchall()]
        monthly_rows = conn.execute(
            f"""SELECT substr(date, 1, 7) AS month, currency,
                       SUM(amount) AS amount, COUNT(*) AS count
                FROM expenses WHERE date >= ? AND date <= ?{scope_sql}
                GROUP BY month, currency ORDER BY month, currency""",
            (start_date, end_date, *scope_params),
        ).fetchall()
        category_rows = conn.execute(
            f"""SELECT category, currency, SUM(amount) AS amount, COUNT(*) AS count
                FROM expenses WHERE date >= ? AND date <= ?{scope_sql}
                GROUP BY category, currency ORDER BY currency, amount DESC, category""",
            (start_date, end_date, *scope_params),
        ).fetchall()
        total_rows = conn.execute(
            f"""SELECT currency, SUM(amount) AS amount, COUNT(*) AS count
                FROM expenses WHERE date >= ? AND date <= ?{scope_sql}
                GROUP BY currency ORDER BY currency""",
            (start_date, end_date, *scope_params),
        ).fetchall()
        centre_rows = []
        if scope["scope_type"] != "user":
            centre_rows = conn.execute(
                f"""SELECT cost_centre, currency, SUM(amount) AS amount, COUNT(*) AS count
                    FROM expenses WHERE date >= ? AND date <= ?{scope_sql}
                    GROUP BY cost_centre, currency ORDER BY cost_centre, currency""",
                (start_date, end_date, *scope_params),
            ).fetchall()

    monthly_index = {
        (row["month"], row["currency"]): {"amount": row["amount"] or 0, "count": row["count"]}
        for row in monthly_rows
    }
    monthly = [
        {
            "month": month,
            "currency": currency,
            **monthly_index.get((month, currency), {"amount": 0, "count": 0}),
        }
        for currency in currencies
        for month in month_keys
    ]
    return {
        "scope": {
            "scope_type": scope["scope_type"],
            "scope_value": scope.get("scope_value"),
        },
        "period": {"start": start_date, "end": end_date},
        "expense_count": sum(row["count"] for row in total_rows),
        "spend_by_currency": [
            {"currency": row["currency"], "amount": row["amount"] or 0, "count": row["count"]}
            for row in total_rows
        ],
        "monthly_spending": monthly,
        "category_spending": [
            {"category": row["category"], "currency": row["currency"], "amount": row["amount"] or 0, "count": row["count"]}
            for row in category_rows
        ],
        "cost_centre_spending": [
            {"cost_centre": row["cost_centre"], "currency": row["currency"], "amount": row["amount"] or 0, "count": row["count"]}
            for row in centre_rows
        ],
        "budget_comparison": {
            "available": False,
            "reason": "Budget records do not define a currency, so they cannot be safely compared with expense amounts.",
        },
    }
