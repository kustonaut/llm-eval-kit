"""Check output length and content density."""

from __future__ import annotations

from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult


class LengthCheck(Check):
    """Validate output length is within acceptable bounds.

    Args:
        min_words: Minimum word count (default 10).
        max_words: Maximum word count (default 5000).
        ideal_min: Ideal lower bound for scoring (default 50).
        ideal_max: Ideal upper bound for scoring (default 2000).
    """

    name = "length"

    def __init__(
        self,
        min_words: int = 10,
        max_words: int = 5000,
        ideal_min: int = 50,
        ideal_max: int = 2000,
    ) -> None:
        self.min_words = min_words
        self.max_words = max_words
        self.ideal_min = ideal_min
        self.ideal_max = ideal_max

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []
        word_count = len(text.split())

        if word_count < self.min_words:
            findings.append(f"Too short: {word_count} words (min {self.min_words})")
        elif word_count > self.max_words:
            findings.append(f"Too long: {word_count} words (max {self.max_words})")

        # Score: 1.0 if in ideal range, degrade linearly outside
        if self.ideal_min <= word_count <= self.ideal_max:
            score = 1.0
        elif word_count < self.ideal_min:
            score = max(0.0, word_count / self.ideal_min)
        else:
            overage = word_count - self.ideal_max
            score = max(0.0, 1.0 - overage / self.ideal_max)

        passed = self.min_words <= word_count <= self.max_words

        return CheckResult(
            name=self.name,
            passed=passed,
            score=round(score, 3),
            findings=findings,
            metadata={"word_count": word_count},
        )
