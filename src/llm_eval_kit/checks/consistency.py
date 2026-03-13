"""Detect self-contradictions within LLM output."""

from __future__ import annotations

import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult

# Contradiction signal patterns
_NEGATION_PAIRS = [
    (r"\bis\b", r"\bis not\b"),
    (r"\bwill\b", r"\bwill not\b"),
    (r"\bcan\b", r"\bcannot\b"),
    (r"\bshould\b", r"\bshould not\b"),
    (r"\bhas\b", r"\bhas no\b"),
    (r"\bincreased\b", r"\bdecreased\b"),
    (r"\bhigher\b", r"\blower\b"),
    (r"\bmore\b", r"\bless\b"),
    (r"\bpositive\b", r"\bnegative\b"),
    (r"\bsuccess\b", r"\bfailure\b"),
    (r"\btrue\b", r"\bfalse\b"),
    (r"\byes\b", r"\bno\b"),
    (r"\balways\b", r"\bnever\b"),
    (r"\beverything\b", r"\bnothing\b"),
    (r"\bimproved\b", r"\bdeclined\b"),
    (r"\bgrew\b", r"\bshrank\b"),
]

_CONTRADICTION_SIGNALS = [
    r"\bhowever,?\s+(?:earlier|previously|above)\s+(?:I|we)\s+(?:said|mentioned|stated)\b",
    r"\bcontrary to (?:what|the) (?:above|previous)\b",
    r"\bthis contradicts\b",
    r"\bon the other hand.*but also\b",
    r"\bboth\s+\w+\s+and\s+not\s+\w+\b",
]

# Numerical contradiction: same entity with different numbers
_NUMBER_PATTERN = re.compile(
    r"(\b(?:revenue|growth|rate|price|cost|count|total|number|percentage|profit|margin|users|customers)\b)"
    r"[^.]{0,40}?"
    r"(\b\d+(?:\.\d+)?%?\b)",
    re.IGNORECASE,
)


class ConsistencyCheck(Check):
    """Detect self-contradictions within LLM output.

    Checks for:
    1. Negation contradictions (says X and not-X)
    2. Numerical contradictions (same metric, different numbers)
    3. Explicit contradiction signals ("however, earlier I said...")

    Args:
        sensitivity: "low" | "medium" | "high" — controls false positive tolerance.
    """

    name = "consistency"

    def __init__(self, sensitivity: str = "medium") -> None:
        self.sensitivity = sensitivity

    def _check_negation_pairs(self, sentences: list[str]) -> list[str]:
        findings = []
        for s1_idx, s1 in enumerate(sentences):
            s1_lower = s1.lower()
            for s2_idx, s2 in enumerate(sentences):
                if s1_idx >= s2_idx:
                    continue
                s2_lower = s2.lower()
                for pos, neg in _NEGATION_PAIRS:
                    if re.search(pos, s1_lower) and re.search(neg, s2_lower):
                        # Check they share at least one significant noun
                        s1_words = set(re.findall(r"\b[a-z]{4,}\b", s1_lower))
                        s2_words = set(re.findall(r"\b[a-z]{4,}\b", s2_lower))
                        overlap = s1_words & s2_words
                        if len(overlap) >= 2:
                            findings.append(
                                f"Potential contradiction: \"{s1[:50]}...\" vs \"{s2[:50]}...\""
                            )
                            break
        return findings

    def _check_numerical(self, text: str) -> list[str]:
        findings = []
        matches = _NUMBER_PATTERN.findall(text.lower())
        if len(matches) >= 2:
            # Group by entity
            entity_values: dict[str, list[str]] = {}
            for entity, value in matches:
                entity = entity.strip().lower()
                entity_values.setdefault(entity, []).append(value)
            for entity, values in entity_values.items():
                unique_values = set(values)
                if len(unique_values) > 1:
                    findings.append(
                        f"Different values for '{entity}': {', '.join(sorted(unique_values))}"
                    )
        return findings

    def _check_explicit_signals(self, text: str) -> list[str]:
        findings = []
        for pattern in _CONTRADICTION_SIGNALS:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    snippet = text[max(0, match.start() - 10):match.end() + 30].strip()
                    findings.append(f"Contradiction signal: ...{snippet}...")
        return findings

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 10]

        # Check for contradictions
        if self.sensitivity in ("medium", "high"):
            findings.extend(self._check_negation_pairs(sentences))

        findings.extend(self._check_numerical(text))
        findings.extend(self._check_explicit_signals(text))

        # Score
        if not findings:
            score = 1.0
        elif len(findings) == 1:
            score = 0.6
        else:
            score = max(0.0, 1.0 - len(findings) * 0.3)

        return CheckResult(
            name=self.name,
            passed=len(findings) == 0,
            score=round(score, 3),
            findings=findings[:5],  # Cap at 5
            metadata={"sentences_analyzed": len(sentences), "contradictions_found": len(findings)},
        )
