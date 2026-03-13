"""Detect unfilled placeholders, template variables, and TODO markers."""

from __future__ import annotations

import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult

_DEFAULT_PATTERNS = [
    (r"\{\{[A-Za-z_][A-Za-z0-9_]*\}\}", "Template variable"),
    (r"\[TBD\]", "TBD marker"),
    (r"\[TODO\]", "TODO marker"),
    (r"\[PLACEHOLDER\]", "Placeholder marker"),
    (r"\[INSERT .+?\]", "Insert instruction"),
    (r"\[FILL IN\]", "Fill-in instruction"),
    (r"(?i)\bLorem ipsum\b", "Lorem ipsum filler"),
    (r"(?i)\bXXX+\b", "XXX placeholder"),
    (r"<YOUR[_ ].*?>", "Template instruction"),
    (r"(?i)\b(replace|update) (this|with your)\b", "Replace instruction"),
]


class PlaceholderCheck(Check):
    """Detect unfilled template variables, TODO markers, and placeholder text.

    Args:
        extra_patterns: Additional (regex, label) tuples.
    """

    name = "placeholder"

    def __init__(self, extra_patterns: list[tuple[str, str]] | None = None) -> None:
        self.patterns = list(_DEFAULT_PATTERNS)
        if extra_patterns:
            self.patterns.extend(extra_patterns)

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []

        for pattern, label in self.patterns:
            matches = re.findall(pattern, text)
            if matches:
                for m in matches[:3]:  # Cap at 3 per pattern
                    findings.append(f"{label}: {m}")

        score = 1.0 if not findings else max(0.0, 1.0 - len(findings) * 0.2)

        return CheckResult(
            name=self.name,
            passed=len(findings) == 0,
            score=round(score, 3),
            findings=findings,
            metadata={"patterns_checked": len(self.patterns), "total_found": len(findings)},
        )
