"""
EvaluationRunner: runs questions through the MCP client, writes actual.json,
compares against expected.json, writes a timestamped report, and shows charts.
"""
from report_viewer import ReportViewer
from shared.model.mcp_client import QuestionResult
from shared.api.api_server_manager import ApiServerManager
from models import (
    EvalReport,
    EvaluationEntry,
    FailureReason,
    QuestionComparison,
)
from mcp_client.mcp_client import MCPClient
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path


class EvaluationRunner:
    def __init__(
        self,
        actual_file: Path = Path(__file__).parent / "actual.json",
        expected_file: Path = Path(__file__).parent / "expected.json",
        output_json: Path = Path(__file__).parent / "output.json",
        output_png: Path = Path(__file__).parent / "output.png",
        batch_size: int = 4,
    ) -> None:
        self.actual_file = actual_file
        self.expected_file = expected_file
        self.output_json = output_json
        self.output_png = output_png
        self.batch_size = batch_size

    async def _run_question(self, client: MCPClient, item: dict) -> EvaluationEntry:
        question = item["question"]
        question_id = item["question_id"]
        print(f"Running Q{question_id}: {question!r}")
        result: QuestionResult = await client.process_question(question, include_toolcalls=True)
        return EvaluationEntry(
            question_id=question_id,
            question=question,
            nl_answer=result.nl_answer,
            tool_calls=result.tool_calls,
        )

    async def _run_questions(self) -> list[EvaluationEntry]:
        inputs: list[dict] = json.loads(self.expected_file.read_text())
        results: list[EvaluationEntry] = []
        async with MCPClient(stateless=True) as client:
            for i in range(0, len(inputs), self.batch_size):
                batch = inputs[i:i + self.batch_size]
                print(
                    f"\nBatch {i // self.batch_size + 1}: running {len(batch)} question(s) concurrently...")
                batch_results = await asyncio.gather(
                    *[self._run_question(client, item) for item in batch]
                )
                results.extend(batch_results)
        return results

    def _compare(self, expected: list[EvaluationEntry], actual: list[EvaluationEntry]) -> EvalReport:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        passing_questions: list[QuestionComparison] = []
        failing_questions: list[QuestionComparison] = []
        total_questions = len(expected)
        questions_with_correct_tools = 0
        questions_with_correct_arguments = 0

        for exp, act in zip(expected, actual):
            expected_calls = exp.tool_calls
            actual_calls = act.tool_calls

            correct_tool_count = sum(
                1 for i, exp_tc in enumerate(expected_calls)
                if i < len(actual_calls) and actual_calls[i].tool_name == exp_tc.tool_name
            )
            all_names_match = (
                len(actual_calls) == len(expected_calls) and
                all(actual_calls[i].tool_name == exp_tc.tool_name
                    for i, exp_tc in enumerate(expected_calls))
            )
            all_args_match = all_names_match and all(
                actual_calls[i].tool_arguments == exp_tc.tool_arguments
                for i, exp_tc in enumerate(expected_calls)
            )
            if all_names_match:
                questions_with_correct_tools += 1
                if all_args_match:
                    questions_with_correct_arguments += 1

            passed = all_names_match and all_args_match
            if passed:
                failure_reason = FailureReason.NONE
            elif not actual_calls:
                failure_reason = FailureReason.NO_TOOL_CALLED
            else:
                failure_reason = FailureReason.WRONG_TOOL_CALLED

            comparison = QuestionComparison(
                question_id=exp.question_id,
                question=exp.question,
                expected_tool_calls=expected_calls,
                actual_tool_calls=actual_calls,
                correct_tool_count=correct_tool_count,
                total_expected_tools=len(expected_calls),
                passed=passed,
                failure_reason=failure_reason,
            )
            if passed:
                passing_questions.append(comparison)
            else:
                failing_questions.append(comparison)

        return EvalReport(
            timestamp=timestamp,
            total_questions=total_questions,
            questions_with_correct_tools=questions_with_correct_tools,
            questions_with_correct_arguments=questions_with_correct_arguments,
            overall_tool_accuracy=questions_with_correct_tools /
            total_questions if total_questions else 0.0,
            overall_argument_accuracy=questions_with_correct_arguments /
            questions_with_correct_tools if questions_with_correct_tools else 0.0,
            passing_questions=passing_questions,
            failing_questions=failing_questions,
        )

    def run(self) -> None:
        with ApiServerManager() as _:
            results = asyncio.run(self._run_questions())

        self.actual_file.write_text(json.dumps(
            [e.to_dict() for e in results], indent=2))
        print(f"\nWrote {len(results)} entries to {self.actual_file}")

        if not self.expected_file.exists():
            print("No expected.json found — skipping comparison.")
            return

        expected_entries = [EvaluationEntry.from_dict(
            e) for e in json.loads(self.expected_file.read_text())]
        actual_entries = [EvaluationEntry.from_dict(
            e) for e in json.loads(self.actual_file.read_text())]
        report = self._compare(expected_entries, actual_entries)

        self.output_json.write_text(json.dumps(report.to_dict(), indent=2))

        print("\n--- Evaluation Report ---")
        print(f"Questions:         {report.total_questions}")
        print(
            f"Correct tools:     {report.questions_with_correct_tools}/{report.total_questions} ({report.overall_tool_accuracy:.0%})")
        print(
            f"Correct arguments: {report.questions_with_correct_arguments}/{report.questions_with_correct_tools} ({report.overall_argument_accuracy:.0%})")
        print(f"\nPassing ({len(report.passing_questions)}):")
        for q in report.passing_questions:
            print(f"  ✓ Q{q.question_id}: {q.question}")
        print(f"\nFailing ({len(report.failing_questions)}):")
        for q in report.failing_questions:
            reason = f" [{q.failure_reason.value.replace('_', ' ')}]" if q.failure_reason != FailureReason.NONE else ""
            print(f"  ✗ Q{q.question_id}: {q.question}{reason}")
        print(f"\nReport written to: {self.output_json}")

        ReportViewer(self.output_png).show(report.to_dict())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP evaluation")
    parser.add_argument("--batch-size", type=int, default=4,
                        help="Number of questions to run concurrently per batch (default: 5)")
    args = parser.parse_args()
    EvaluationRunner(batch_size=args.batch_size).run()
