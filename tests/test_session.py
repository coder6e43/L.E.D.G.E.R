import pytest

from auth.authentication import AuthenticatedUser
from auth.session import get_current_user, is_authenticated, logout, set_authenticated_user


@pytest.fixture(autouse=True)
def clear_session():
    logout()
    yield
    logout()


def test_session_lifecycle():
    user = AuthenticatedUser("U001", "Test", "test@example.com", "Employee", "CC-TECH")
    assert get_current_user() is None
    assert not is_authenticated()
    set_authenticated_user(user)
    assert get_current_user() is user
    assert is_authenticated()
    logout()
    assert get_current_user() is None
    assert not is_authenticated()


def test_session_rejects_request_shaped_user():
    with pytest.raises(TypeError):
        set_authenticated_user({"user_id": "U001", "role": "Admin", "cost_centre": "CC-SALES"})

