"""Detect hallucination markers in LLM output."""

from __future__ import annotations

import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult

# Phrases that indicate the model is hedging or fabricating
_DEFAULT_MARKERS = [
    r"(?i)\bas of my (knowledge|training) cutoff\b",
    r"(?i)\bI don'?t have (access|information|data) (to|about|on)\b",
    r"(?i)\bI'?m not (sure|certain|able to verify)\b",
    r"(?i)\bthis (is|may be) speculative\b",
    r"(?i)\bI cannot (confirm|verify|validate)\b",
    r"(?i)\bplease (verify|check|confirm) (this|with)\b",
    r"(?i)\baccording to my (training|knowledge)\b",
    r"(?i)\bI (believe|think|assume) (that |this )?(?:might|could|may)\b",
    r"(?i)\bnote:?\s*I (don'?t|cannot|can'?t) (access|browse|search)\b",
]

# Phrases that indicate invented citations or fake references
_CITATION_MARKERS = [
    r"(?i)\b(Smith|Johnson|Brown) et al\.?,?\s*\(?\d{4}\)?\b",  # generic "et al." citations
    r"(?i)\baccording to a (\d{4} )?study\b",
    r"(?i)\bresearch (shows|suggests|indicates) that\b",
    r"(?i)\bsources?:?\s*(unavailable|not available|n/?a)\b",
]


class HallucinationCheck(Check):
    """Detect hedging, fabrication markers, and fake citations in LLM output.

    Args:
        extra_markers: Additional regex patterns to detect.
        check_citations: Whether to check for fabricated citations.
        threshold: Score threshold for pass/fail (default 1.0 = no markers allowed).
    """

    name = "hallucination"

    def __init__(
        self,
        extra_markers: list[str] | None = None,
        check_citations: bool = True,
        threshold: float = 1.0,
    ) -> None:
        self.markers = list(_DEFAULT_MARKERS)
        if extra_markers:
            self.markers.extend(extra_markers)
        self.check_citations = check_citations
        self.threshold = threshold

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []

        for pattern in self.markers:
            matches = re.findall(pattern, text)
            if matches:
                # Get the first match for readable reporting
                match = re.search(pattern, text)
                if match:
                    snippet = text[max(0, match.start() - 20):match.end() + 20].strip()
                    findings.append(f"Hedging marker: ...{snippet}...")

        if self.check_citations:
            for pattern in _CITATION_MARKERS:
                matches = re.findall(pattern, text)
                if matches:
                    match = re.search(pattern, text)
                    if match:
                        snippet = text[max(0, match.start() - 10):match.end() + 10].strip()
                        findings.append(f"Possible fabricated citation: ...{snippet}...")

        total_checks = len(self.markers) + (len(_CITATION_MARKERS) if self.check_citations else 0)
        score = 1.0 - (len(findings) / max(total_checks, 1))
        score = max(0.0, min(1.0, score))

        return CheckResult(
            name=self.name,
            passed=score >= self.threshold,
            score=round(score, 3),
            findings=findings,
            metadata={"markers_checked": total_checks, "markers_found": len(findings)},
        )
