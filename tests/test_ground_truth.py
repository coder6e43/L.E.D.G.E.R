from tests.ground_truth import ground_truth, budget_truth


def test_tech_food_september():
    gt = ground_truth("CC-TECH", category="Food", start="2026-09-01", end="2026-09-30")
    assert gt["result"] == 1350.0
    assert gt["source_row_ids"] == ["EXP-1002", "EXP-1005"]


def test_duplicate_not_double_counted():
    assert ground_truth("CC-TECH", category="Food")["row_count"] == 2


def test_tech_total_excludes_invalid_category():
    gt = ground_truth("CC-TECH")
    assert gt["result"] == 5750.0
    assert gt["source_row_ids"] == ["EXP-1001", "EXP-1002", "EXP-1003", "EXP-1005"]


def test_marketing_excludes_invalid_date():
    gt = ground_truth("CC-MARKETING")
    assert gt["result"] == 5000.0
    assert gt["source_row_ids"] == ["EXP-1004"]


def test_single_day():
    gt = ground_truth("CC-TECH", start="2026-09-10", end="2026-09-10")
    assert gt["result"] == 450.0
    assert gt["source_row_ids"] == ["EXP-1002"]


def test_zero_rows():
    gt = ground_truth("CC-TECH", start="2026-07-01", end="2026-07-31")
    assert gt["result"] == 0.0 and gt["source_row_ids"] == []


def test_budget_food():
    b = budget_truth("CC-TECH", "Food", "2026-09-01", "2026-09-30")
    assert b["remaining"] == 3650.0 and b["burn_rate"] == 27.0


def test_budget_travel():
    b = budget_truth("CC-TECH", "Travel", "2026-09-01", "2026-09-30")
    assert b["remaining"] == 6800.0 and b["burn_rate"] == 32.0


def test_budget_missing_returns_none():
    assert budget_truth("CC-TECH", "Marketing", "2026-09-01", "2026-09-30") is None
