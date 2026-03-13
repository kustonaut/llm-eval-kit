"""Base class for all quality checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """Result of a single quality check."""

    name: str
    passed: bool
    score: float  # 0.0 (worst) to 1.0 (best)
    findings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        detail = f" — {'; '.join(self.findings)}" if self.findings else ""
        return f"[{status}] {self.name}: {self.score:.2f}{detail}"


class Check(ABC):
    """Base class for pluggable quality checks.

    Subclass and implement `run()` to create a custom check.

    Example:
        class MyCheck(Check):
            name = "my_check"

            def run(self, text: str, **context) -> CheckResult:
                issues = []
                if "TODO" in text:
                    issues.append("Contains TODO")
                score = 0.0 if issues else 1.0
                return CheckResult(
                    name=self.name,
                    passed=len(issues) == 0,
                    score=score,
                    findings=issues,
                )
    """

    name: str = "base_check"

    @abstractmethod
    def run(self, text: str, **context: Any) -> CheckResult:
        """Run the check against the given text.

        Args:
            text: The LLM output to evaluate.
            **context: Additional context (prompt, model, metadata).

        Returns:
            CheckResult with pass/fail, score, and findings.
        """
        ...
