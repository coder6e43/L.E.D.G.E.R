from database.connection import get_connection


def test_intentional_bad_expense_rows_are_reported_and_not_inserted(sample_database):
    result = sample_database["results"]["expenses"]
    assert result["inserted"] == 136
    assert len(result["errors"]) == 4
    assert any("duplicate expense_id" in error for error in result["errors"])
    assert any("invalid date" in error for error in result["errors"])
    assert any("invalid category" in error for error in result["errors"])
    assert any("amount cannot be negative" in error for error in result["errors"])

    with get_connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE expense_id = ?", ("EXP-1136",)
        ).fetchone()[0] == 1
        for rejected_id in ("EXP-1137", "EXP-1138", "EXP-1139"):
            assert conn.execute(
                "SELECT COUNT(*) FROM expenses WHERE expense_id = ?", (rejected_id,)
            ).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 136


def test_sample_users_and_budgets_ingest_without_errors(sample_database):
    results = sample_database["results"]
    assert results["users"]["inserted"] == 110
    assert results["users"]["errors"] == []
    assert results["budgets"]["inserted"] == 120
    assert results["budgets"]["errors"] == []
