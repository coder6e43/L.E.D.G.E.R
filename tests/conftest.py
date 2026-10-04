from pathlib import Path

import pytest

from database import connection
from database.ingestion import ingest_budgets, ingest_expenses, ingest_users
from database.models import init_db


@pytest.fixture
def sample_database(tmp_path, monkeypatch):
    """Load the project samples into an isolated SQLite database."""
    monkeypatch.chdir(tmp_path)
    database_path = tmp_path / "data" / "ledger-test.db"
    monkeypatch.setattr(connection, "DB_PATH", str(database_path))
    init_db()

    data_dir = Path(__file__).resolve().parents[1] / "data"
    results = {
        "users": ingest_users(str(data_dir / "sample_users.csv")),
        "expenses": ingest_expenses(str(data_dir / "sample_expenses.csv")),
        "budgets": ingest_budgets(str(data_dir / "sample_budgets.csv")),
    }
    return {"path": database_path, "results": results}
