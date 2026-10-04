import sqlite3
import pandas as pd
import pytest

from calculation import engine
from calculation.engine import run_calculation
from tests.ground_truth import ground_truth, load_clean_expenses, budget_truth

T, M = "CC-TECH", "CC-MARKETING"
BUDGETS = pd.read_csv("data/sample_budgets.csv")
COST_CENTRES = sorted(load_clean_expenses()["cost_centre"].unique())


def build_db(path, extra_expenses=()):
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE expenses (expense_id TEXT, user_id TEXT,
        cost_centre TEXT, category TEXT, amount REAL, currency TEXT,
        date TEXT, description TEXT)""")
    conn.execute("""CREATE TABLE budgets (budget_id TEXT, cost_centre TEXT,
        category TEXT, amount REAL, period_start TEXT, period_end TEXT)""")
    df = load_clean_expenses()
    rows = [(r.expense_id, r.user_id, r.cost_centre, r.category, r.amount,
             r.currency, r.date, r.description) for r in df.itertuples()]
    conn.executemany("INSERT INTO expenses VALUES (?,?,?,?,?,?,?,?)",
                     rows + list(extra_expenses))
    conn.executemany("INSERT INTO budgets VALUES (?,?,?,?,?,?)",
                     [tuple(x) for x in BUDGETS.itertuples(index=False)])
    conn.commit()
    conn.close()


@pytest.fixture
def use_db(tmp_path, monkeypatch):
    def _use(extra_expenses=()):
        path = tmp_path / "engine_test.db"
        if path.exists():
            path.unlink()
        build_db(path, extra_expenses)

        def fake_conn():
            c = sqlite3.connect(path)
            c.row_factory = sqlite3.Row
            return c
        monkeypatch.setattr(engine, "get_connection", fake_conn)
    _use()
    return _use


def q(intent, cc, **kw):
    d = {"intent": intent, "user_scope": cc}
    d.update(kw)
    return d


SUM_CASES = [
    dict(cost_centre=T, category="Food", start="2026-09-01", end="2026-09-30"),
    dict(cost_centre=T, category="Travel", start="2026-09-01", end="2026-09-30"),
    dict(cost_centre=T, category="Software", start="2026-09-01", end="2026-09-30"),
    dict(cost_centre=T, start="2026-09-01", end="2026-09-30"),
    dict(cost_centre=T, start="2026-09-01", end="2026-09-15"),
    dict(cost_centre=T, start="2026-09-10", end="2026-09-10"),
    dict(cost_centre=T, start="2026-09-20", end="2026-09-20"),
    dict(cost_centre=T, start="2026-07-01", end="2026-07-31"),
    dict(cost_centre=T, start="2026-07-01", end="2026-09-20"),
    dict(cost_centre=M, category="Marketing", start="2026-09-01", end="2026-09-30"),
    dict(cost_centre=M, start="2026-08-15", end="2026-09-15"),
    dict(cost_centre=T, start="2025-01-01", end="2025-01-31"),
]


@pytest.mark.parametrize("c", SUM_CASES)
def test_sum_matches_ground_truth(use_db, c):
    exp = ground_truth(**c)
    got = run_calculation(q("sum_expenses", c["cost_centre"],
                            category=c.get("category"),
                            date_range_start=c.get("start"),
                            date_range_end=c.get("end")), c["cost_centre"])
    assert got["status"] == "SUCCESS"
    assert got["result"] == pytest.approx(exp["result"])
    assert sorted(got["source_rows"]) == exp["source_row_ids"]
    assert got["row_count"] == exp["row_count"]


def test_zero_rows_is_explicit_zero(use_db):
    got = run_calculation(q("sum_expenses", T, date_range_start="2025-01-01",
                            date_range_end="2025-01-31"), T)
    assert got["status"] == "SUCCESS" and got["result"] == 0
    assert got["source_rows"] == []


def test_count_matches_ground_truth(use_db):
    exp = ground_truth(T, category="Food")
    got = run_calculation(q("count_expenses", T, category="Food"), T)
    assert got["result"] == exp["row_count"]
    assert sorted(got["source_rows"]) == exp["source_row_ids"]


def test_category_breakdown(use_db):
    df = load_clean_expenses()
    expected = df[df["cost_centre"] == T].groupby("category")["amount"].sum().to_dict()
    got = run_calculation(q("category_breakdown", T), T)
    assert got["status"] == "SUCCESS"
    assert got["result"] == pytest.approx(expected)


def test_top_three_by_amount(use_db):
    df = load_clean_expenses()
    df = df[(df["cost_centre"] == T) & (df["_date"] >= "2026-09-01")
            & (df["_date"] <= "2026-09-30")]
    expected = sorted(df["amount"].tolist(), reverse=True)[:3]
    got = run_calculation(q("top_transactions", T, limit=3,
                            date_range_start="2026-09-01",
                            date_range_end="2026-09-30"), T)
    assert [r["amount"] for r in got["result"]] == expected
    assert len(got["source_rows"]) == len(expected)


def test_source_lookup_returns_exact_rows(use_db):
    exp = ground_truth(T, category="Food", start="2026-09-01", end="2026-09-30")
    got = run_calculation(q("source_lookup", T, category="Food",
                            date_range_start="2026-09-01",
                            date_range_end="2026-09-30"), T)
    assert sorted(got["source_rows"]) == exp["source_row_ids"]


BUDGET_CASES = [tuple(r) for r in BUDGETS[
    ["cost_centre", "category", "period_start", "period_end"]].itertuples(index=False)]


@pytest.mark.parametrize("cc,cat,ps,pe", BUDGET_CASES)
def test_remaining_budget_and_burn_rate(use_db, cc, cat, ps, pe):
    exp = budget_truth(cc, cat, ps, pe)
    base = dict(category=cat, date_range_start=ps, date_range_end=pe)
    rem = run_calculation(q("remaining_budget", cc, **base), cc)
    assert rem["status"] == "SUCCESS"
    assert rem["result"] == pytest.approx(exp["remaining"])
    assert rem["spend"] == pytest.approx(exp["spend"])
    assert sorted(rem["source_rows"]) == exp["source_row_ids"]
    burn = run_calculation(q("burn_rate", cc, **base), cc)
    assert burn["result"] == pytest.approx(exp["burn_rate"], abs=0.01)


def test_missing_budget_is_not_zero(use_db):
    got = run_calculation(q("remaining_budget", T, category="Snacks",
                            date_range_start="2026-09-01",
                            date_range_end="2026-09-30"), T)
    assert got["status"] == "BUDGET_NOT_FOUND"
    assert got["result"] is None and got["source_rows"] == []

def test_scope_conflict_rejected(use_db):
    got = run_calculation(q("sum_expenses", M), T)
    assert got["status"] == "USER_SCOPE_CONFLICT"
    assert got["result"] is None and got["source_rows"] == []


@pytest.mark.parametrize("cc", COST_CENTRES)
def test_no_cross_cost_centre_leakage(use_db, cc):
    df = load_clean_expenses()
    forbidden = set(df[df["cost_centre"] != cc]["expense_id"])
    for intent in ("sum_expenses", "source_lookup", "count_expenses"):
        got = run_calculation({"intent": intent}, cc)
        assert got["source_rows"], "expected some rows for " + cc
        assert not set(got["source_rows"]) & forbidden


def test_missing_authorized_scope_rejected(use_db):
    assert run_calculation({"intent": "sum_expenses"}, "")["status"] == "MISSING_AUTHORIZED_SCOPE"


def test_invalid_date_rejected(use_db):
    got = run_calculation(q("sum_expenses", T, date_range_start="2026-13-40"), T)
    assert got["status"] == "INVALID_DATE" and got["result"] is None


def test_unknown_intent_rejected(use_db):
    assert run_calculation({"intent": "predict_spend"}, T)["status"] == "UNKNOWN_INTENT"


def test_mixed_currency_refused_unless_filtered(use_db):
    use_db(extra_expenses=[("EXP-9001", "U001", T, "Food", 10.0, "USD",
                            "2026-09-11", "USD lunch")])
    df = load_clean_expenses()
    inr_expected = df[(df["cost_centre"] == T) & (df["category"] == "Food")
                      & (df["currency"] == "INR")]["amount"].sum()
    mixed = run_calculation(q("sum_expenses", T, category="Food"), T)
    assert mixed["status"] == "MIXED_CURRENCY" and mixed["result"] is None
    inr = run_calculation(q("sum_expenses", T, category="Food", currency="INR"), T)
    assert inr["status"] == "SUCCESS"
    assert inr["result"] == pytest.approx(inr_expected)
    assert "EXP-9001" not in inr["source_rows"]
