# coding: utf-8
import pytest
import openapi_client
from openapi_client.api.user_api import UserApi
from openapi_client.models.user import User

BASE_URL = "http://localhost:8080/v2"


@pytest.fixture
def user_api():
    config = openapi_client.Configuration(host=BASE_URL)
    with openapi_client.ApiClient(config) as client:
        yield UserApi(client)


def test_get_user_by_name_seed_data(user_api):
    """Seed user 'user1' should be retrievable."""
    user = user_api.get_user_by_name("user1")
    assert user.username == "user1"
    assert user.first_name == "Alice"


def test_get_user_by_name_not_found(user_api):
    """Non-existent username returns 404."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        user_api.get_user_by_name("doesnotexist")
    assert exc_info.value.status == 404


def test_login_user_valid(user_api):
    """Valid credentials return a session token string."""
    token = user_api.login_user("user1", "abc123")
    assert "user1" in token


def test_login_user_invalid(user_api):
    """Invalid credentials return 400."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        user_api.login_user("user1", "wrongpassword")
    assert exc_info.value.status == 400


def test_logout_user(user_api):
    """Logout endpoint returns successfully."""
    user_api.logout_user()  # should not raise


def test_create_user(user_api):
    """Creating a new user stores it."""
    new_user = User(username="testuser", first_name="Test", last_name="User",
                    email="test@example.com", password="pass1", phone="555-9999",
                    user_status=1)
    user_api.create_user(new_user)
    fetched = user_api.get_user_by_name("testuser")
    assert fetched.username == "testuser"
    assert fetched.email == "test@example.com"
    # clean up
    user_api.delete_user("testuser")


def test_create_users_with_array_input(user_api):
    """Creating multiple users via array stores all of them."""
    users = [
        User(username="arrayuser1", password="p1", user_status=1),
        User(username="arrayuser2", password="p2", user_status=1),
    ]
    user_api.create_users_with_array_input(users)
    assert user_api.get_user_by_name("arrayuser1").username == "arrayuser1"
    assert user_api.get_user_by_name("arrayuser2").username == "arrayuser2"
    # clean up
    user_api.delete_user("arrayuser1")
    user_api.delete_user("arrayuser2")


def test_create_users_with_list_input(user_api):
    """Creating multiple users via list stores all of them."""
    users = [
        User(username="listuser1", password="p1", user_status=1),
        User(username="listuser2", password="p2", user_status=1),
    ]
    user_api.create_users_with_list_input(users)
    assert user_api.get_user_by_name("listuser1").username == "listuser1"
    assert user_api.get_user_by_name("listuser2").username == "listuser2"
    # clean up
    user_api.delete_user("listuser1")
    user_api.delete_user("listuser2")


def test_update_user(user_api):
    """Updating a user's details persists."""
    user = User(username="updateme", first_name="Before",
                password="pw", user_status=1)
    user_api.create_user(user)
    updated = User(username="updateme", first_name="After",
                   password="pw", user_status=1)
    user_api.update_user("updateme", updated)
    fetched = user_api.get_user_by_name("updateme")
    assert fetched.first_name == "After"
    # clean up
    user_api.delete_user("updateme")


def test_delete_user(user_api):
    """Deleting a user removes it from the store."""
    user = User(username="deleteme", password="pw", user_status=1)
    user_api.create_user(user)
    user_api.delete_user("deleteme")
    with pytest.raises(openapi_client.ApiException) as exc_info:
        user_api.get_user_by_name("deleteme")
    assert exc_info.value.status == 404


def test_delete_user_not_found(user_api):
    """Deleting a non-existent user returns 404."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        user_api.delete_user("ghostuser")
    assert exc_info.value.status == 404
