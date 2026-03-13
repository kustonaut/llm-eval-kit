"""Generate markdown reports from eval results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llm_eval_kit.scorer import ScoreCard
from llm_eval_kit.eval_runner import SuiteResult
from llm_eval_kit.compare import ComparisonResult


class MarkdownReporter:
    """Generate markdown reports from eval results.

    Usage:
        reporter = MarkdownReporter()

        # From a scorecard
        md = reporter.scorecard_report(scorecard)

        # From a suite result
        md = reporter.suite_report(suite_result)

        # From a comparison
        md = reporter.comparison_report(comparison_result)

        # Save to file
        reporter.save(md, "report.md")
    """

    def scorecard_report(self, scorecard: ScoreCard, title: str = "Eval Report") -> str:
        status = "PASS ✅" if scorecard.passed else "FAIL ❌"
        lines = [
            f"# {title}",
            "",
            f"**Overall Score:** {scorecard.overall_score:.2f} / 1.00 ({status})",
            f"**Threshold:** {scorecard.threshold}",
            f"**Checks Passed:** {scorecard.passed_checks} / {scorecard.total_checks}",
            "",
            "## Check Results",
            "",
            "| Check | Score | Status | Findings |",
            "|-------|-------|--------|----------|",
        ]

        for check in scorecard.checks:
            status_icon = "✅" if check.passed else "❌"
            findings = "; ".join(check.findings[:3]) if check.findings else "—"
            lines.append(f"| {check.name} | {check.score:.2f} | {status_icon} | {findings} |")

        return "\n".join(lines)

    def suite_report(self, result: SuiteResult, title: str | None = None) -> str:
        title = title or f"Eval Suite: {result.name}"
        lines = [
            f"# {title}",
            "",
            f"**Pass Rate:** {result.passed}/{result.total} ({result.pass_rate:.0%})",
            f"**Average Score:** {result.avg_score:.2f}",
            "",
            "## Test Results",
            "",
            "| Test | Score | Status | Findings |",
            "|------|-------|--------|----------|",
        ]

        for r in result.results:
            status_icon = "✅" if r.overall_pass else "❌"
            findings = "; ".join(r.findings[:2]) if r.findings else "—"
            lines.append(f"| {r.test_case.name} | {r.scorecard.overall_score:.2f} | {status_icon} | {findings} |")

        # Failed tests detail
        failed = [r for r in result.results if not r.overall_pass]
        if failed:
            lines.extend(["", "## Failed Tests", ""])
            for r in failed:
                lines.append(f"### {r.test_case.name}")
                lines.append(f"**Score:** {r.scorecard.overall_score:.2f}")
                if r.findings:
                    for f in r.findings[:5]:
                        lines.append(f"- {f}")
                lines.append("")

        return "\n".join(lines)

    def comparison_report(self, result: ComparisonResult) -> str:
        lines = [
            "# Model Comparison Report",
            "",
            f"**Prompt:** {result.prompt[:200]}",
            f"**Winner:** {result.winner}",
            "",
            "## Rankings",
            "",
            "| Rank | Model | Score | Latency |",
            "|------|-------|-------|---------|",
        ]

        for rank, (model, score) in enumerate(result.rankings, 1):
            model_result = next(r for r in result.results if r.model_name == model)
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
            lines.append(f"| {medal} | {model} | {score:.2f} | {model_result.latency_ms:.0f}ms |")

        # Per-check breakdown
        if result.results:
            check_names = [c.name for c in result.results[0].scorecard.checks]
            lines.extend(["", "## Per-Check Breakdown", ""])
            header = "| Model |"
            for cn in check_names:
                header += f" {cn} |"
            lines.append(header)
            lines.append("|" + "|".join(["-------"] * (len(check_names) + 1)) + "|")

            for r in sorted(result.results, key=lambda x: -x.scorecard.overall_score):
                row = f"| {r.model_name} |"
                for check in r.scorecard.checks:
                    row += f" {check.score:.2f} |"
                lines.append(row)

        return "\n".join(lines)

    def save(self, content: str, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
