import pandas as pd
import pytest
from tests.ground_truth import (ground_truth, budget_truth, load_clean_expenses,
                                VALID_CATEGORIES, EXPENSES_CSV)

CLEAN = load_clean_expenses()
RAW = pd.read_csv(EXPENSES_CSV)
CENTRES = sorted(CLEAN["cost_centre"].unique())


def test_categories_match_ingestion_rules():
    ingestion = pytest.importorskip("database.ingestion")
    assert VALID_CATEGORIES == set(ingestion.ALLOWED_CATEGORIES)


def test_duplicates_removed():
    assert not CLEAN["expense_id"].duplicated().any()
    assert RAW["expense_id"].duplicated().sum() >= 1   # the dirty row exists


def test_invalid_rows_excluded():
    assert "EXP-1137" not in set(CLEAN["expense_id"])           # Snacks
    assert CLEAN["_date"].notna().all()                          # bad date gone
    assert set(CLEAN["category"]) <= VALID_CATEGORIES


def test_cost_centres_add_up_to_grand_total():
    parts = sum(ground_truth(cc)["result"] for cc in CENTRES)
    assert parts == pytest.approx(round(float(CLEAN["amount"].sum()), 2))


def test_no_row_belongs_to_two_centres():
    ids = [i for cc in CENTRES for i in ground_truth(cc)["source_row_ids"]]
    assert len(ids) == len(set(ids)) == len(CLEAN)


@pytest.mark.parametrize("cc", CENTRES)
def test_categories_add_up_to_centre_total(cc):
    total = ground_truth(cc)["result"]
    parts = sum(ground_truth(cc, category=c)["result"]
                for c in VALID_CATEGORIES)
    assert parts == pytest.approx(total)


def test_split_date_ranges_add_up():
    cc = CENTRES[0]
    whole = ground_truth(cc, start="2026-07-01", end="2026-09-30")
    a = ground_truth(cc, start="2026-07-01", end="2026-08-31")
    b = ground_truth(cc, start="2026-09-01", end="2026-09-30")
    assert whole["result"] == pytest.approx(a["result"] + b["result"])
    assert whole["row_count"] == a["row_count"] + b["row_count"]


def test_single_day_only_includes_that_day():
    day = CLEAN["_date"].iloc[0]
    iso = day.strftime("%Y-%m-%d")
    gt = ground_truth(CLEAN["cost_centre"].iloc[0], start=iso, end=iso)
    assert gt["row_count"] >= 1


def test_zero_rows():
    gt = ground_truth(CENTRES[0], start="2025-01-01", end="2025-01-31")
    assert gt["result"] == 0.0 and gt["source_row_ids"] == []


def test_budget_identities():
    b = pd.read_csv("data/sample_budgets.csv").iloc[0]
    got = budget_truth(b.cost_centre, b.category, b.period_start, b.period_end)
    assert got["remaining"] == pytest.approx(got["budget"] - got["spend"], abs=0.01)
    assert got["burn_rate"] == pytest.approx(got["spend"] / got["budget"] * 100, abs=0.01)


def test_missing_budget_returns_none():
    assert budget_truth("CC-TECH", "Snacks", "2026-09-01", "2026-09-30") is None
