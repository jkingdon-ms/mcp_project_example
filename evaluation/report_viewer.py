import json
import subprocess
import sys
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import numpy as np
from matplotlib.patches import Patch


class ReportViewer:
    def __init__(self, output_png: Path = Path(__file__).parent / "output.png") -> None:
        self.output_png = output_png

    def load_output(self) -> dict:
        path = Path(__file__).parent / "output.json"
        if not path.exists():
            print("No output.json found")
            sys.exit(1)
        print(f"Loading: {path}")
        return json.loads(path.read_text())

    def load(self, path: Path) -> dict:
        print(f"Loading: {path}")
        return json.loads(path.read_text())

    def show(self, report: dict) -> None:
        total = report["total_questions"]
        correct_tools = report["questions_with_correct_tools"]
        tool_acc = report["overall_tool_accuracy"]  # noqa: F841
        arg_acc = report["overall_argument_accuracy"]  # noqa: F841
        passing_questions = report["passing_questions"]
        failing_questions = report["failing_questions"]
        # Sort all questions by question_id for consistent x-axis ordering
        question_results = sorted(
            passing_questions + failing_questions, key=lambda r: r["question_id"]
        )

        labels = [f"Q{r['question_id']}" for r in question_results]
        per_q_tool_acc = [
            r["correct_tool_count"] / r["total_expected_tools"]
            if r["total_expected_tools"] > 0 else 0.0
            for r in question_results
        ]
        per_q_arg_acc = []
        for r in question_results:
            comparisons = r["tool_call_comparisons"]
            correct_tool_comparisons = [
                c for c in comparisons if c["tool_name_match"]]
            if not correct_tool_comparisons:
                per_q_arg_acc.append(0.0)
            else:
                per_q_arg_acc.append(
                    sum(1 for c in correct_tool_comparisons if c["tool_arguments_match"]) /
                    len(correct_tool_comparisons)
                )

        fig = plt.figure(figsize=(14, 14))
        fig.suptitle(
            f"Evaluation Report  —  {report['timestamp']}", fontsize=14, fontweight="bold")
        # 3 rows: overall accuracy, clustered per-Q chart, full-width table
        gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.35,
                               height_ratios=[1, 1, 1.1])

        # 1a. Tool accuracy pie
        correct_args = report["questions_with_correct_arguments"]
        ax1 = fig.add_subplot(gs[0, 0])
        wrong_tools = total - correct_tools
        ax1.pie(
            [correct_tools, wrong_tools],
            labels=[f"Correct\n({correct_tools})",
                    f"Incorrect\n({wrong_tools})"],
            colors=["#4C9BE8", "#CFD8DC"],
            autopct="%1.0f%%",
            startangle=90,
        )
        ax1.set_title("Tool Accuracy")

        # 1b. Argument accuracy pie (denominator = questions with correct tools)
        ax2 = fig.add_subplot(gs[0, 1])
        wrong_args = correct_tools - correct_args
        if correct_tools > 0:
            ax2.pie(
                [correct_args, wrong_args],
                labels=[f"Correct\n({correct_args})",
                        f"Incorrect\n({wrong_args})"],
                colors=["#E87B4C", "#CFD8DC"],
                autopct="%1.0f%%",
                startangle=90,
            )
        else:
            ax2.text(0.5, 0.5, "N/A", ha="center", va="center", fontsize=14,
                     transform=ax2.transAxes)
        ax2.set_title("Argument Accuracy\n(of questions with correct tool)")

        # 2. Clustered per-question bar chart: Tool Accuracy + Argument Accuracy side by side
        ax_pq = fig.add_subplot(gs[1, :])
        x = np.arange(len(labels))
        bar_w = 0.35
        ax_pq.bar(x - bar_w / 2, per_q_tool_acc, bar_w,
                  label="Tool Accuracy", color="#4C9BE8")
        ax_pq.bar(x + bar_w / 2, per_q_arg_acc, bar_w,
                  label="Argument Accuracy", color="#E87B4C")
        ax_pq.set_ylim(0, 1.15)
        ax_pq.set_ylabel("Accuracy")
        ax_pq.set_title("Per-Question Accuracy")
        ax_pq.set_xticks(x)
        ax_pq.set_xticklabels(labels)
        ax_pq.axhline(y=1.0, color="grey", linestyle="--", linewidth=0.8)
        ax_pq.legend(handles=[
            Patch(color="#4C9BE8", label="Tool Accuracy"),
            Patch(color="#E87B4C", label="Argument Accuracy"),
        ], fontsize=8, loc="upper right")

        # Bottom row: full-width results table
        ax_table = fig.add_subplot(gs[2, :])
        ax_table.axis("off")
        ax_table.set_title("Question Results", fontsize=10,
                           fontweight="bold", pad=8)

        all_results = sorted(passing_questions +
                             failing_questions, key=lambda r: r["question_id"])
        table_data = []
        cell_colors = []
        green = "#C8E6C9"
        red = "#FFCDD2"
        white = "#FFFFFF"
        for r in all_results:
            status = "PASS" if r["passed"] else "FAIL"
            reason_val = r.get("failure_reason", "")
            reason = reason_val.replace("_", " ") if reason_val else ""
            table_data.append(
                [f"Q{r['question_id']}", r["question"], status, reason])
            row_color = green if r["passed"] else red
            cell_colors.append([white, white, row_color, white])

        table = ax_table.table(
            cellText=table_data,
            colLabels=["ID", "Question", "Status", "Reason"],
            cellLoc="left",
            loc="center",
            bbox=Bbox([[0, 0], [1, 1]]),
            cellColours=cell_colors,
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.auto_set_column_width([0, 1, 2, 3])
        # Style header row
        for col in range(4):
            table[0, col].set_facecolor("#37474F")
            table[0, col].set_text_props(color="white", fontweight="bold")

        chart_path = self.output_png
        plt.savefig(chart_path, bbox_inches="tight", dpi=150)
        print(f"Chart saved to {chart_path}")
        # Open the chart as a new tab in VS Code
        subprocess.Popen(["code", str(chart_path)])
        plt.show()


if __name__ == "__main__":
    viewer = ReportViewer()
    if len(sys.argv) > 1:
        report = viewer.load(Path(sys.argv[1]))
    else:
        report = viewer.load_output()
    viewer.show(report)
