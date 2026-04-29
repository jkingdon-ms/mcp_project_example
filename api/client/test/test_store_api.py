# coding: utf-8
import pytest
import openapi_client
from openapi_client.api.store_api import StoreApi
from openapi_client.models.order import Order

BASE_URL = "http://localhost:8080/v2"


@pytest.fixture
def store_api():
    config = openapi_client.Configuration(host=BASE_URL)
    with openapi_client.ApiClient(config) as client:
        yield StoreApi(client)


def test_get_inventory(store_api):
    """Inventory returns a dict mapping status strings to counts."""
    inventory = store_api.get_inventory()
    assert isinstance(inventory, dict)
    # Seed data: 2 available, 1 sold
    assert inventory.get("available", 0) >= 2
    assert inventory.get("sold", 0) >= 1


def test_get_order_by_id_seed_data(store_api):
    """Seed order 1 (delivered) should be retrievable."""
    order = store_api.get_order_by_id(1)
    assert order.id == 1
    assert order.status == "delivered"
    assert order.complete is True


def test_get_order_by_id_not_found(store_api):
    """Non-existent order returns 404 (uses ID 5, which is in valid spec range 1-10)."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        store_api.get_order_by_id(5)
    assert exc_info.value.status == 404


def test_place_order(store_api):
    """Placing an order stores it and returns it with an id."""
    order = Order(pet_id=2, quantity=1, status="placed", complete=False)
    placed = store_api.place_order(order)
    assert placed.id is not None
    assert placed.status == "placed"
    assert placed.pet_id == 2
    # clean up
    store_api.delete_order(placed.id)


def test_delete_order(store_api):
    """Deleting an order removes it from the store."""
    order = Order(pet_id=1, quantity=2, status="placed", complete=False)
    placed = store_api.place_order(order)
    store_api.delete_order(placed.id)
    with pytest.raises(openapi_client.ApiException) as exc_info:
        store_api.get_order_by_id(placed.id)
    assert exc_info.value.status == 404


def test_delete_order_not_found(store_api):
    """Deleting a non-existent order returns 404."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        store_api.delete_order(99999)
    assert exc_info.value.status == 404
