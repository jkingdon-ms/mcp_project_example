import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.user import User  # noqa: E501
from openapi_server import util
from openapi_server import store


def _save_user(user: User):
    if user.id is None:
        user.id = store.next_user_id()
    store.users[user.username] = user


def create_user(body):  # noqa: E501
    """Create user

    :param body: Created user object
    :type body: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = User.from_dict(connexion.request.get_json())  # noqa: E501
    if not isinstance(body, User) or not body.username:
        return 'Invalid user supplied', 400
    _save_user(body)
    return None, 200


def create_users_with_array_input(body):  # noqa: E501
    """Creates list of users with given input array

    :param body: List of user object
    :type body: list | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = [User.from_dict(d) for d in connexion.request.get_json()]  # noqa: E501
    for user in body:
        _save_user(user)
    return None, 200


def create_users_with_list_input(body):  # noqa: E501
    """Creates list of users with given input array

    :param body: List of user object
    :type body: list | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = [User.from_dict(d) for d in connexion.request.get_json()]  # noqa: E501
    for user in body:
        _save_user(user)
    return None, 200


def delete_user(username):  # noqa: E501
    """Delete user

    :param username: The name that needs to be deleted
    :type username: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if username not in store.users:
        return 'User not found', 404
    del store.users[username]
    return None, 200


def get_user_by_name(username):  # noqa: E501
    """Get user by user name

    :param username: The name that needs to be fetched.
    :type username: str

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    user = store.users.get(username)
    if user is None:
        return 'User not found', 404
    return user, 200


def login_user(username, password):  # noqa: E501
    """Logs user into the system

    :param username: The user name for login
    :type username: str
    :param password: The password for login in clear text
    :type password: str

    :rtype: Union[str, Tuple[str, int], Tuple[str, int, Dict[str, str]]
    """
    user = store.users.get(username)
    if user is None or user.password != password:
        return 'Invalid username/password supplied', 400
    return f'logged_in:{username}', 200


def logout_user():  # noqa: E501
    """Logs out current logged in user session

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return None, 200


def update_user(username, body):  # noqa: E501
    """Updated user

    :param username: name that need to be updated
    :type username: str
    :param body: Updated user object
    :type body: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = User.from_dict(connexion.request.get_json())  # noqa: E501
    if not isinstance(body, User):
        return 'Invalid user supplied', 400
    if username not in store.users:
        return 'User not found', 404
    body.username = username
    if body.id is None:
        body.id = store.users[username].id
    store.users[username] = body
    return None, 200
