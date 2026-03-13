"""Quality scorer — runs all checks and produces an aggregate score."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult
from llm_eval_kit.checks.hallucination import HallucinationCheck
from llm_eval_kit.checks.placeholder import PlaceholderCheck
from llm_eval_kit.checks.style import StyleCheck
from llm_eval_kit.checks.freshness import FreshnessCheck
from llm_eval_kit.checks.length import LengthCheck


@dataclass
class ScoreCard:
    """Aggregate results from all checks."""

    checks: list[CheckResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    threshold: float = 0.7

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "passed": self.passed,
            "threshold": self.threshold,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "checks": [
                {"name": c.name, "passed": c.passed, "score": c.score, "findings": c.findings}
                for c in self.checks
            ],
        }

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"ScoreCard: {self.overall_score:.2f} [{status}] ({self.passed_checks}/{self.total_checks} checks passed)"]
        for c in self.checks:
            lines.append(f"  {c}")
        return "\n".join(lines)


class Scorer:
    """Run quality checks against LLM output and produce a scorecard.

    Usage:
        scorer = Scorer()  # uses default checks
        scorecard = scorer.score("The LLM output text here...")

        # Custom checks:
        scorer = Scorer(checks=[HallucinationCheck(), PlaceholderCheck()])

        # With context:
        scorecard = scorer.score(output, prompt="original prompt", model="gpt-4o")
    """

    def __init__(
        self,
        checks: list[Check] | None = None,
        threshold: float = 0.7,
    ) -> None:
        self.checks = checks or self._default_checks()
        self.threshold = threshold

    @staticmethod
    def _default_checks() -> list[Check]:
        return [
            HallucinationCheck(),
            PlaceholderCheck(),
            StyleCheck(),
            FreshnessCheck(),
            LengthCheck(),
        ]

    def score(self, text: str, **context: Any) -> ScoreCard:
        """Run all checks and produce an aggregate scorecard.

        Args:
            text: The LLM output to evaluate.
            **context: Additional context passed to each check (prompt, model, etc.).
        """
        results = [check.run(text, **context) for check in self.checks]

        if results:
            overall = sum(r.score for r in results) / len(results)
        else:
            overall = 1.0

        return ScoreCard(
            checks=results,
            overall_score=round(overall, 3),
            passed=overall >= self.threshold,
            threshold=self.threshold,
        )

    def add_check(self, check: Check) -> None:
        """Add a check to the scorer."""
        self.checks.append(check)
