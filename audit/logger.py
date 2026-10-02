import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path("data/audit.db")
VALID_STATUSES = {"SUCCESS", "REFUSED", "CLARIFY", "ACCESS_DENIED"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS query_audit (
    query_id          TEXT PRIMARY KEY,
    timestamp         TEXT NOT NULL,
    user_id           TEXT NOT NULL,
    scope             TEXT NOT NULL,
    raw_prompt        TEXT NOT NULL,
    parsed_json       TEXT,
    applied_filters   TEXT,
    source_row_ids    TEXT,
    numeric_result    REAL,
    execution_status  TEXT NOT NULL,
    latency_ms        INTEGER
);
"""


def init_db(db_path=DEFAULT_DB):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def log_query(user_id, scope, raw_prompt, status, parsed_query=None,
              applied_filters=None, source_row_ids=None,
              numeric_result=None, latency_ms=None, db_path=DEFAULT_DB):
    """Write one audit record and return its query_id."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    if status == "SUCCESS" and source_row_ids is None:
        raise ValueError("SUCCESS records must include source_row_ids")

    init_db(db_path)
    query_id = str(uuid.uuid4())
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO query_audit VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                query_id,
                datetime.now(timezone.utc).isoformat(),
                user_id,
                scope,
                raw_prompt,
                json.dumps(parsed_query) if parsed_query is not None else None,
                json.dumps(applied_filters) if applied_filters is not None else None,
                json.dumps(source_row_ids) if source_row_ids is not None else None,
                numeric_result,
                status,
                latency_ms,
            ),
        )
        conn.commit()
    return query_id


def get_audit_record(query_id, db_path=DEFAULT_DB):
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM query_audit WHERE query_id = ?", (query_id,)
        ).fetchone()
    if row is None:
        return None
    rec = dict(row)
    for key in ("parsed_json", "applied_filters", "source_row_ids"):
        if rec[key] is not None:
            rec[key] = json.loads(rec[key])
    return rec


def get_recent(limit=20, db_path=DEFAULT_DB):
    """Latest records, for the 'show audit trail' demo step."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM query_audit ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
