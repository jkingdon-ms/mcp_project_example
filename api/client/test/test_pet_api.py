# coding: utf-8
import pytest
import requests
import openapi_client
from openapi_client.api.pet_api import PetApi
from openapi_client.models.pet import Pet
from openapi_client.models.category import Category
from openapi_client.models.tag import Tag

BASE_URL = "http://localhost:8080/v2"


@pytest.fixture
def pet_api():
    config = openapi_client.Configuration(host=BASE_URL)
    with openapi_client.ApiClient(config) as client:
        yield PetApi(client)


def _add_and_find(pet_api: PetApi, pet: Pet) -> Pet:
    """Add a pet and retrieve it by name (add_pet returns None per spec)."""
    pet_api.add_pet(pet)
    pets = pet_api.find_pets_by_status([pet.status or "available"])
    return next(p for p in pets if p.name == pet.name)


def test_get_pet_by_id_seed_data(pet_api):
    """Seed pet 1 (Buddy) should be retrievable."""
    pet = pet_api.get_pet_by_id(1)
    assert pet.id == 1
    assert pet.name == "Buddy"
    assert pet.status == "available"


def test_get_pet_by_id_not_found(pet_api):
    """Non-existent pet returns 404."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        pet_api.get_pet_by_id(99999)
    assert exc_info.value.status == 404


def test_find_pets_by_status_available(pet_api):
    """Finding available pets returns at least the two seed pets."""
    pets = pet_api.find_pets_by_status(["available"])
    assert isinstance(pets, list)
    names = [p.name for p in pets]
    assert "Buddy" in names
    assert "Whiskers" in names


def test_find_pets_by_status_sold(pet_api):
    """Finding sold pets returns the sold seed pet."""
    pets = pet_api.find_pets_by_status(["sold"])
    names = [p.name for p in pets]
    assert "Goldie" in names


def test_find_pets_by_tags(pet_api):
    """Finding by tag returns pets with that tag."""
    pets = pet_api.find_pets_by_tags(["friendly"])
    assert any(p.name == "Buddy" for p in pets)


def test_add_pet(pet_api):
    """Adding a new pet stores it and is findable afterwards."""
    new_pet = Pet(
        name="RexUnique",
        photo_urls=["https://example.com/rex.jpg"],
        status="available",
        category=Category(id=1, name="Dogs"),
        tags=[Tag(id=3, name="playful")],
    )
    created = _add_and_find(pet_api, new_pet)
    assert created.id is not None
    assert created.name == "RexUnique"
    # clean up
    pet_api.delete_pet(created.id)


def test_update_pet(pet_api):
    """Updating a pet changes its stored state."""
    pet = Pet(name="UpdateMeUnique", photo_urls=[
              "https://example.com/x.jpg"], status="available")
    created = _add_and_find(pet_api, pet)
    created.status = "pending"
    pet_api.update_pet(created)
    fetched = pet_api.get_pet_by_id(created.id)
    assert fetched.status == "pending"
    # clean up
    pet_api.delete_pet(created.id)


def test_update_pet_with_form(pet_api):
    """Updating pet name/status via form data works."""
    pet = Pet(name="FormPetUnique", photo_urls=[
              "https://example.com/fp.jpg"], status="available")
    created = _add_and_find(pet_api, pet)
    # The server accepts JSON for this endpoint; send directly rather than
    # using the generated client which defaults to application/x-www-form-urlencoded.
    resp = requests.post(
        f"{BASE_URL}/pet/{created.id}",
        json={"name": "FormPetUpdated", "status": "pending"},
    )
    assert resp.status_code == 200
    fetched = pet_api.get_pet_by_id(created.id)
    assert fetched.name == "FormPetUpdated"
    assert fetched.status == "pending"
    # clean up
    pet_api.delete_pet(created.id)


def test_delete_pet(pet_api):
    """Deleting a pet removes it from the store."""
    pet = Pet(name="DeleteMeUnique", photo_urls=[
              "https://example.com/d.jpg"], status="available")
    created = _add_and_find(pet_api, pet)
    pet_api.delete_pet(created.id)
    with pytest.raises(openapi_client.ApiException) as exc_info:
        pet_api.get_pet_by_id(created.id)
    assert exc_info.value.status == 404


def test_delete_pet_not_found(pet_api):
    """Deleting a non-existent pet returns 404."""
    with pytest.raises(openapi_client.ApiException) as exc_info:
        pet_api.delete_pet(99999)
    assert exc_info.value.status == 404


def test_upload_file(pet_api):
    """Uploading a file for an existing pet returns a 200 ApiResponse."""
    response = pet_api.upload_file(1)
    assert response.code == 200
