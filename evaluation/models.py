from dataclasses import dataclass
from enum import Enum

from dataclasses_json import DataClassJsonMixin

from shared.model.mcp_client import ToolCall


class FailureReason(str, Enum):
    NONE = ""
    NO_TOOL_CALLED = "no_tool_called"
    WRONG_TOOL_CALLED = "wrong_tool_called"


@dataclass
class EvaluationEntry(DataClassJsonMixin):
    question_id: int
    question: str
    tool_calls: list[ToolCall]
    nl_answer: str = ""


@dataclass
class QuestionComparison(DataClassJsonMixin):
    question_id: int
    question: str
    expected_tool_calls: list[ToolCall]
    actual_tool_calls: list[ToolCall]
    correct_tool_count: int
    total_expected_tools: int
    passed: bool = False
    failure_reason: FailureReason = FailureReason.NONE


@dataclass
class EvalReport(DataClassJsonMixin):
    timestamp: str
    total_questions: int
    questions_with_correct_tools: int
    questions_with_correct_arguments: int
    overall_tool_accuracy: float
    overall_argument_accuracy: float
    passing_questions: list[QuestionComparison]
    failing_questions: list[QuestionComparison]
