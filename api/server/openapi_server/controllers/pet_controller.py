import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.api_response import ApiResponse  # noqa: E501
from openapi_server.models.pet import Pet  # noqa: E501
from openapi_server import util
from openapi_server import store


def add_pet(body):  # noqa: E501
    """Add a new pet to the store

    :param body: Pet object that needs to be added to the store
    :type body: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = Pet.from_dict(connexion.request.get_json())  # noqa: E501
    if not isinstance(body, Pet):
        return 'Invalid input', 405
    if body.id is None:
        body.id = store.next_pet_id()
    store.pets[body.id] = body
    return body, 200


def delete_pet(pet_id):  # noqa: E501
    """Deletes a pet

    :param pet_id: Pet id to delete
    :type pet_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if pet_id not in store.pets:
        return 'Pet not found', 404
    del store.pets[pet_id]
    return None, 200


def find_pets_by_status(status):  # noqa: E501
    """Finds Pets by status

    Multiple status values can be provided with comma separated strings

    :param status: Status values that need to be considered for filter
    :type status: List[str]

    :rtype: Union[List[Pet], Tuple[List[Pet], int], Tuple[List[Pet], int, Dict[str, str]]
    """
    if not status:
        return 'Invalid status value', 400
    return [p for p in store.pets.values() if p.status in status], 200


def find_pets_by_tags(tags):  # noqa: E501
    """Finds Pets by tags

    Multiple tags can be provided with comma separated strings.

    :param tags: Tags to filter by
    :type tags: List[str]

    :rtype: Union[List[Pet], Tuple[List[Pet], int], Tuple[List[Pet], int, Dict[str, str]]
    """
    if not tags:
        return 'Invalid tag value', 400
    result = []
    for pet in store.pets.values():
        pet_tag_names = {t.name for t in (pet.tags or []) if t.name}
        if pet_tag_names & set(tags):
            result.append(pet)
    return result, 200


def get_pet_by_id(pet_id):  # noqa: E501
    """Find pet by ID

    Returns a single pet

    :param pet_id: ID of pet to return
    :type pet_id: int

    :rtype: Union[Pet, Tuple[Pet, int], Tuple[Pet, int, Dict[str, str]]
    """
    pet = store.pets.get(pet_id)
    if pet is None:
        return 'Pet not found', 404
    return pet, 200


def update_pet(body):  # noqa: E501
    """Update an existing pet

    :param body: Pet object that needs to be added to the store
    :type body: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        body = Pet.from_dict(connexion.request.get_json())  # noqa: E501
    if not isinstance(body, Pet):
        return 'Invalid input', 405
    if body.id is None or body.id not in store.pets:
        return 'Pet not found', 404
    store.pets[body.id] = body
    return body, 200


def update_pet_with_form(pet_id, name=None, status=None):  # noqa: E501
    """Updates a pet in the store with form data

    :param pet_id: ID of pet that needs to be updated
    :type pet_id: int
    :param name: Updated name of the pet
    :type name: str
    :param status: Updated status of the pet
    :type status: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    pet = store.pets.get(pet_id)
    # connexion 2.x may not unpack formData into kwargs; fall back to request.form
    if name is None:
        name = connexion.request.form.get('name')
    if status is None:
        status = connexion.request.form.get('status')
    if pet is None:
        return 'Pet not found', 404
    if name is not None:
        pet.name = name
    if status is not None:
        pet.status = status
    return None, 200


def upload_file(pet_id, additional_metadata=None, file=None):  # noqa: E501
    """uploads an image

    :param pet_id: ID of pet to update
    :type pet_id: int
    :param additional_metadata: Additional data to pass to server
    :type additional_metadata: str
    :param file: file to upload
    :type file: str

    :rtype: Union[ApiResponse, Tuple[ApiResponse, int], Tuple[ApiResponse, int, Dict[str, str]]
    """
    if pet_id not in store.pets:
        return 'Pet not found', 404
    msg = 'File uploaded'
    if additional_metadata:
        msg += f'; additionalMetadata: {additional_metadata}'
    return ApiResponse(code=200, type='unknown', message=msg), 200
