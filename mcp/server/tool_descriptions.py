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
    "find_pets_by_status": (
        "Use this tool to search for pets by their status (available, pending, sold). "
        "When a user asks about a specific pet by name (e.g. 'Tell me about Buddy'), "
        "query with each status value to retrieve all pets, then filter by name. "
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
    "get_inventory": (
        "Use this tool to get a count of pets grouped by status. "
        "Use when the user asks about stock levels, inventory, or how many pets are available."
    ),
    "get_order_by_id": (
        "Use this tool to look up the details of a specific order by its numeric ID. "
        "Use when the user asks about the status or details of an order."
    ),
    "place_order": (
        "Use this tool to place a new purchase order for a pet. "
        "Requires a pet ID and quantity at minimum."
    ),
    "get_user_by_name": (
        "Use this tool to retrieve a user's profile by their username. "
        "Use when the user asks about account details or a specific user."
    ),
    "login_user": (
        "Use this tool to authenticate a user with a username and password. "
        "Use when the user wants to log in or check credentials."
    ),
})
