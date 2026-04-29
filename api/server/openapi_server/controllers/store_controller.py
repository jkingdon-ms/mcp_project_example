import connexion
from collections import Counter
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.order import Order  # noqa: E501
from openapi_server import util
from openapi_server import store


def delete_order(order_id):  # noqa: E501
    """Delete purchase order by ID

    :param order_id: ID of the order that needs to be deleted
    :type order_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if order_id not in store.orders:
        return 'Order not found', 404
    del store.orders[order_id]
    return None, 200


def get_inventory():  # noqa: E501
    """Returns pet inventories by status

    Returns a map of status codes to quantities

    :rtype: Union[Dict[str, int], Tuple[Dict[str, int], int], Tuple[Dict[str, int], int, Dict[str, str]]
    """
    counts = Counter(p.status for p in store.pets.values() if p.status)
    return dict(counts), 200


def get_order_by_id(order_id):  # noqa: E501
    """Find purchase order by ID

    :param order_id: ID of the order that needs to be fetched
    :type order_id: int

    :rtype: Union[Order, Tuple[Order, int], Tuple[Order, int, Dict[str, str]]
    """
    order = store.orders.get(order_id)
    if order is None:
        return 'Order not found', 404
    return order, 200


def place_order(body):  # noqa: E501
    """Place an order for a pet

    :param body: order placed for purchasing the pet
    :type body: dict | bytes

    :rtype: Union[Order, Tuple[Order, int], Tuple[Order, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = Order.from_dict(connexion.request.get_json())  # noqa: E501
    if not isinstance(body, Order):
        return 'Invalid Order', 400
    if body.id is None:
        body.id = store.next_order_id()
    store.orders[body.id] = body
    return body, 200
