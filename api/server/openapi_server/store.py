"""Shared in-memory data store for all controllers."""

from openapi_server.models.pet import Pet
from openapi_server.models.category import Category
from openapi_server.models.tag import Tag
from openapi_server.models.order import Order
from openapi_server.models.user import User

# dict of pet_id (int) -> Pet
pets = {
    1: Pet(id=1, name='Buddy', status='available',
           category=Category(id=1, name='Dogs'),
           photo_urls=['https://example.com/buddy.jpg'],
           tags=[Tag(id=1, name='friendly')]),
    2: Pet(id=2, name='Whiskers', status='available',
           category=Category(id=2, name='Cats'),
           photo_urls=['https://example.com/whiskers.jpg'],
           tags=[Tag(id=2, name='indoor')]),
    3: Pet(id=3, name='Goldie', status='sold',
           category=Category(id=3, name='Fish'),
           photo_urls=['https://example.com/goldie.jpg'],
           tags=[]),
}

# dict of order_id (int) -> Order
orders = {
    1: Order(id=1, pet_id=3, quantity=1, status='delivered', complete=True),
    2: Order(id=2, pet_id=1, quantity=1, status='placed', complete=False),
}

# dict of username (str) -> User
users = {
    'user1': User(id=1, username='user1', first_name='Alice', last_name='Smith',
                  email='alice@example.com', password='abc123', phone='555-0100', user_status=1),
    'admin': User(id=2, username='admin', first_name='Bob', last_name='Jones',
                  email='bob@example.com', password='admin123', phone='555-0101', user_status=1),
}

# Monotonically increasing ID counters
_pet_id_counter = 4
_order_id_counter = 3
_user_id_counter = 3


def next_pet_id() -> int:
    global _pet_id_counter
    val = _pet_id_counter
    _pet_id_counter += 1
    return val


def next_order_id() -> int:
    global _order_id_counter
    val = _order_id_counter
    _order_id_counter += 1
    return val


def next_user_id() -> int:
    global _user_id_counter
    val = _user_id_counter
    _user_id_counter += 1
    return val
