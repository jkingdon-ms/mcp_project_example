from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin


@dataclass
class ToolCall(DataClassJsonMixin):
    tool_name: str
    tool_arguments: dict
    tool_response: dict


@dataclass
class QuestionResult(DataClassJsonMixin):
    nl_answer: str
    tool_calls: list[ToolCall]
