"""Detect AI-typical phrasing and enforce voice style rules."""

from __future__ import annotations

import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult

_DEFAULT_AI_TELLS = [
    (r"(?i)\bI'?d be happy to\b", "AI tell: 'I'd be happy to'"),
    (r"(?i)\bLet me know if you need\b", "AI tell: 'Let me know if you need'"),
    (r"(?i)\bIn today'?s (world|landscape|environment)\b", "AI tell: filler opener"),
    (r"(?i)\bIt'?s worth noting\b", "AI tell: filler phrase"),
    (r"(?i)\bCertainly!?\b", "AI tell: 'Certainly'"),
    (r"(?i)\bAbsolutely!?\b", "AI tell: 'Absolutely'"),
    (r"(?i)\bOf course!?\b", "AI tell: 'Of course'"),
    (r"(?i)\bGreat question\b", "AI tell: 'Great question'"),
    (r"(?i)\bI hope this helps\b", "AI tell: 'I hope this helps'"),
    (r"(?i)\bFeel free to\b", "AI tell: 'Feel free to'"),
    (r"(?i)\bAs an AI\b", "AI tell: self-references as AI"),
    (r"(?i)\bdelve (into|deeper)\b", "AI tell: 'delve'"),
    (r"(?i)\btapestry\b", "AI tell: 'tapestry'"),
    (r"(?i)\blandscape of\b", "AI tell: 'landscape of'"),
]


class StyleCheck(Check):
    """Detect AI-typical phrasing patterns and enforce custom voice rules.

    Args:
        anti_patterns: Override default AI tell patterns with custom (regex, label) list.
        extra_patterns: Additional patterns to append to defaults.
    """

    name = "style"

    def __init__(
        self,
        anti_patterns: list[tuple[str, str]] | None = None,
        extra_patterns: list[tuple[str, str]] | None = None,
    ) -> None:
        if anti_patterns is not None:
            self.patterns = list(anti_patterns)
        else:
            self.patterns = list(_DEFAULT_AI_TELLS)
        if extra_patterns:
            self.patterns.extend(extra_patterns)

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []

        for pattern, label in self.patterns:
            if re.search(pattern, text):
                findings.append(label)

        score = 1.0 - (len(findings) / max(len(self.patterns), 1))
        score = max(0.0, min(1.0, score))

        return CheckResult(
            name=self.name,
            passed=len(findings) == 0,
            score=round(score, 3),
            findings=findings,
            metadata={"patterns_checked": len(self.patterns), "ai_tells_found": len(findings)},
        )
