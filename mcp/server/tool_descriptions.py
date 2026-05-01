import dataclasses


@dataclasses.dataclass
class ToolDescriptions:
    """
    Maps tool names to additional description hints for LLM optimization.
    These are appended to the base tool description in _customize_components.
    """
    descriptions: dict[str, str] = dataclasses.field(default_factory=dict)

    def get(self, tool_name: str) -> str | None:
        return self.descriptions.get(tool_name)


CUSTOM_TOOL_DESCRIPTIONS = ToolDescriptions(descriptions={
    # Comment out any of these descriptions to see the evaluation results when tools are called correctly vs incorrectly.
    # These descriptions help the model choose the right tool for the right question.
    # For example, commenting out the 'find_pets_by_status' description will usually cause 1 or 2 questions to fail in evaluation.

    # ── Pet tools ────────────────────────────────────────────────────────────
    "add_pet": (
        "Use this tool to add a new pet to the store. "
        "Requires at minimum a name and photo URL. "
        "Optionally accepts a category, tags, and status (default: available)."
    ),
    "update_pet": (
        "Use this tool to fully replace an existing pet record. "
        "Requires the complete pet object including its ID. "
        "Use update_pet_with_form instead when only updating name or status."
    ),
    "update_pet_with_form": (
        "Use this tool to update only the name or status of an existing pet using its numeric ID. "
        "Prefer this over update_pet when the user asks to change a pet's name or status. "
        "Valid status values are exactly: 'available', 'pending', 'sold' (always lowercase). "
        "Example: to mark a pet as sold, call update_pet_with_form(pet_id=<id>, status='sold')."
    ),
    "find_pets_by_status": (
        "Use this tool to search for pets by their status (available, pending, sold). "
        "When a user asks about a specific pet by name (e.g. 'Tell me about Buddy'), "
        "call once with status=['available', 'pending', 'sold'] to retrieve all pets, then filter by name. "
        "When a user asks about pets of a specific category or type (e.g. 'What cats are available?'), "
        "use the status mentioned in the query (e.g. 'available'), then filter results by category name."
    ),
    "find_pets_by_tags": (
        "Use this tool to find pets that have a specific tag (e.g. 'friendly', 'indoor'). "
        "Use when a user asks about pets with certain characteristics or labels."
    ),
    "get_pet_by_id": (
        "Use this tool when you already know the numeric ID of a pet. "
        "Prefer find_pets_by_status when only a name is known."
    ),
    "delete_pet": (
        "Use this tool to permanently delete a pet from the store by its numeric ID. "
        "Use when the user asks to remove or delete a specific pet."
    ),
    "upload_file": (
        "Use this tool to attach an image to an existing pet record. "
        "Requires the pet's numeric ID and the image file."
    ),

    # ── Store / order tools ──────────────────────────────────────────────────
    "get_inventory": (
        "Use this tool to get a count of pets grouped by status. "
        "Use when the user asks about stock levels, inventory, or how many pets are available."
    ),
    "place_order": (
        "Use this tool to place a new purchase order for a pet. "
        "Requires a pet ID and quantity at minimum."
    ),
    "get_order_by_id": (
        "Use this tool to look up the details of a specific order by its numeric ID. "
        "Use when the user asks about the status or details of an order."
    ),
    "delete_order": (
        "Use this tool to cancel and delete a purchase order by its numeric ID. "
        "Use when the user asks to cancel or remove an order."
    ),

    # ── User tools ───────────────────────────────────────────────────────────
    "create_user": (
        "Use this tool to create a single new user account. "
        "Use when the user asks to register or add a new user."
    ),
    "create_users_with_array_input": (
        "Use this tool to create multiple user accounts from an array. "
        "Use when the user wants to bulk-register users."
    ),
    "create_users_with_list_input": (
        "Use this tool to create multiple user accounts from a list. "
        "Equivalent to create_users_with_array_input; use either for bulk user creation."
    ),
    "login_user": (
        "Use this tool to authenticate a user with a username and password. "
        "Use when the user wants to log in or check credentials."
    ),
    "logout_user": (
        "Use this tool to log out the currently authenticated user. "
        "Use when the user asks to log out or end their session."
    ),
    "get_user_by_name": (
        "Use this tool to retrieve a user's profile by their username. "
        "Use when the user asks about account details or a specific user."
    ),
    "update_user": (
        "Use this tool to update an existing user's profile by their username. "
        "Use when the user asks to change account details such as email, phone, or name."
    ),
    "delete_user": (
        "Use this tool to permanently delete a user account by username. "
        "Use when the user asks to remove or deregister a user."
    ),
})
