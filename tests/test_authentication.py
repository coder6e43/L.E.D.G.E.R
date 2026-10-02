import bcrypt
import pytest

from auth.authentication import AuthenticatedUser, authenticate_user
from database import connection
from database.connection import get_connection
from database.models import init_db


@pytest.fixture
def user_db(tmp_path, monkeypatch):
    monkeypatch.setattr(connection, "DB_PATH", str(tmp_path / "ledger-test.db"))
    init_db()
    password = "Correct horse battery staple"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()
    with connection.get_connection() as conn:
        conn.execute(
            """INSERT INTO users (user_id, name, email, password_hash, role, cost_centre)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("U001", "Test User", "test@example.com", password_hash, "Employee", "CC-TECH"),
        )
    return password


def test_valid_credentials_return_safe_identity(user_db, caplog):
    user = authenticate_user("TEST@example.com", user_db)
    assert isinstance(user, AuthenticatedUser)
    assert user.to_dict() == {
        "user_id": "U001",
        "name": "Test User",
        "email": "test@example.com",
        "role": "Employee",
        "cost_centre": "CC-TECH",
    }
    assert "password_hash" not in user.to_dict()
    assert user_db not in repr(user)
    assert user_db not in caplog.text


@pytest.mark.parametrize(
    ("email", "password"),
    [("test@example.com", "wrong"), ("unknown@example.com", "wrong"), ("", ""), (" ", "pw")],
)
def test_invalid_credentials_fail_without_detail(user_db, email, password):
    assert authenticate_user(email, password) is None


def test_sql_injection_in_email_is_treated_as_data(user_db):
    assert authenticate_user("' OR 1=1 --", user_db) is None


def test_authenticated_user_cannot_be_fabricated_from_request_fields():
    with pytest.raises(TypeError):
        AuthenticatedUser("U001", "Attacker", "x@example.com", "Admin", "CC-SALES")


def test_sample_placeholder_hash_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(connection, "DB_PATH", str(tmp_path / "placeholder.db"))
    init_db()
    with connection.get_connection() as conn:
        conn.execute(
            """INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)""",
            ("U002", "Demo User", "demo@example.com", "hashed_pw_2", "Manager", "CC-SALES"),
        )
    assert authenticate_user("demo@example.com", "anything") is None


def test_updated_sample_user_accepts_documented_password(sample_database):
    with get_connection() as conn:
        row = conn.execute("SELECT email FROM users ORDER BY user_id LIMIT 1").fetchone()
    user = authenticate_user(row["email"], "Password123!")
    assert isinstance(user, AuthenticatedUser)
    assert "password_hash" not in user.to_dict()


def test_updated_sample_user_rejects_wrong_password(sample_database):
    with get_connection() as conn:
        row = conn.execute("SELECT email FROM users ORDER BY user_id LIMIT 1").fetchone()
    assert authenticate_user(row["email"], "wrong password") is None


