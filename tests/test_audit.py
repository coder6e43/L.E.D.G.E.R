import pytest
from audit.logger import log_query, get_audit_record, get_recent


@pytest.fixture
def db(tmp_path):
    return tmp_path / "audit_test.db"


def test_success_record_roundtrip(db):
    qid = log_query(
        user_id="U-001", scope="CC-TECH",
        raw_prompt="How much did I spend on food this month?",
        status="SUCCESS",
        parsed_query={"intent": "sum_expenses", "category": "Food"},
        applied_filters={"cost_centre": "CC-TECH", "category": "Food"},
        source_row_ids=["EXP-1002", "EXP-1042"],
        numeric_result=4820.0, latency_ms=42, db_path=db,
    )
    rec = get_audit_record(qid, db_path=db)
    assert rec["user_id"] == "U-001"
    assert rec["scope"] == "CC-TECH"
    assert rec["parsed_json"]["intent"] == "sum_expenses"
    assert rec["source_row_ids"] == ["EXP-1002", "EXP-1042"]
    assert rec["numeric_result"] == 4820.0
    assert rec["execution_status"] == "SUCCESS"
    assert rec["timestamp"]


def test_zero_rows_success_allowed(db):
    qid = log_query("U-001", "CC-TECH", "food in Jan", "SUCCESS",
                    source_row_ids=[], numeric_result=0.0, db_path=db)
    assert get_audit_record(qid, db_path=db)["source_row_ids"] == []


def test_success_without_source_rows_rejected(db):
    with pytest.raises(ValueError):
        log_query("U-001", "CC-TECH", "x", "SUCCESS", db_path=db)


def test_invalid_status_rejected(db):
    with pytest.raises(ValueError):
        log_query("U-001", "CC-TECH", "x", "MAYBE", db_path=db)


@pytest.mark.parametrize("status", ["REFUSED", "CLARIFY", "ACCESS_DENIED"])
def test_non_success_states_logged(db, status):
    qid = log_query("U-001", "CC-TECH", "predict next month", status, db_path=db)
    rec = get_audit_record(qid, db_path=db)
    assert rec["execution_status"] == status
    assert rec["numeric_result"] is None


def test_get_recent_orders_newest_first(db):
    log_query("U-001", "CC-TECH", "first", "CLARIFY", db_path=db)
    log_query("U-001", "CC-TECH", "second", "CLARIFY", db_path=db)
    assert get_recent(db_path=db)[0]["raw_prompt"] == "second"
