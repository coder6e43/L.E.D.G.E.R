import pandas as pd

EXPENSES_CSV = "data/sample_expenses.csv"
BUDGETS_CSV = "data/sample_budgets.csv"
VALID_CATEGORIES = {"Software", "Food", "Travel", "Marketing"}


def load_clean_expenses(csv_path=EXPENSES_CSV):
    """Apply the ingestion rules: no duplicates, valid dates, valid categories."""
    df = pd.read_csv(csv_path)
    date_col = "expense_date" if "expense_date" in df.columns else "date"
    df["_date"] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["_date"])
    df = df[df["category"].isin(VALID_CATEGORIES)]
    df = df.drop_duplicates(subset="expense_id", keep="first")
    return df


def ground_truth(cost_centre, category=None, start=None, end=None,
                 approved_only=True, csv_path=EXPENSES_CSV):
    """Independent pandas calculation used ONLY in tests."""
    df = load_clean_expenses(csv_path)
    df = df[df["cost_centre"] == cost_centre]
    if approved_only and "status" in df.columns:
        df = df[df["status"].str.lower() == "approved"]
    if category:
        df = df[df["category"] == category]
    if start:
        df = df[df["_date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["_date"] <= pd.Timestamp(end)]
    return {
        "result": round(float(df["amount"].sum()), 2),
        "row_count": len(df),
        "source_row_ids": sorted(df["expense_id"].tolist()),
    }


def budget_truth(cost_centre, category, period_start, period_end,
                 budgets_csv=BUDGETS_CSV):
    """Remaining = budget - spend; burn rate = spend / budget * 100."""
    b = pd.read_csv(budgets_csv)
    amt_col = "budget_amount" if "budget_amount" in b.columns else "amount"
    b = b[(b["cost_centre"] == cost_centre) & (b["category"] == category)
          & (b["period_start"] == period_start) & (b["period_end"] == period_end)]
    if b.empty:
        return None  # no budget set: the product must refuse
    budget = float(b[amt_col].iloc[0])
    spend = ground_truth(cost_centre, category, period_start, period_end)
    return {
        "budget": budget,
        "spend": spend["result"],
        "remaining": round(budget - spend["result"], 2),
        "burn_rate": round(spend["result"] / budget * 100, 2) if budget else None,
        "source_row_ids": spend["source_row_ids"],
    }
