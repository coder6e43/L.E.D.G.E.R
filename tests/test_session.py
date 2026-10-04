import pytest
from contextvars import Context

from auth import get_current_user as package_get_current_user
from auth import is_authenticated as package_is_authenticated
from auth import logout as package_logout
from auth import set_authenticated_user as package_set_authenticated_user
from auth.authentication import AuthenticatedUser
from auth.session import get_current_user, is_authenticated, logout, set_authenticated_user


@pytest.fixture(autouse=True)
def clear_session():
    logout()
    yield
    logout()


def test_session_lifecycle():
    user = AuthenticatedUser._from_database(
        {"user_id": "U001", "name": "Test", "email": "test@example.com",
         "role": "Employee", "cost_centre": "CC-TECH"}
    )
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


def test_package_exports_session_lifecycle():
    user = AuthenticatedUser._from_database(
        {"user_id": "U001", "name": "Test", "email": "test@example.com",
         "role": "Employee", "cost_centre": "CC-TECH"}
    )
    package_set_authenticated_user(user)
    assert package_get_current_user() is user
    assert package_is_authenticated()
    package_logout()
    assert package_get_current_user() is None


def test_authenticated_identity_isolated_from_a_fresh_execution_context():
    user = AuthenticatedUser._from_database(
        {"user_id": "U001", "name": "Test", "email": "test@example.com",
         "role": "Employee", "cost_centre": "CC-TECH"}
    )
    set_authenticated_user(user)
    assert get_current_user() is user
    assert Context().run(get_current_user) is None
