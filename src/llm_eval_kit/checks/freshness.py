"""Check for stale dates and outdated temporal references."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult


class FreshnessCheck(Check):
    """Detect outdated dates and temporal references in LLM output.

    Args:
        current_year: Override auto-detected current year.
        stale_years: Years considered stale (default: anything before current year - 1).
    """

    name = "freshness"

    def __init__(self, current_year: int | None = None, stale_years: int = 1) -> None:
        self.current_year = current_year or datetime.now(timezone.utc).year
        self.stale_threshold = self.current_year - stale_years

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []

        # Find 4-digit years in text
        year_matches = re.findall(r"\b(20[0-9]{2})\b", text)
        stale_years = [int(y) for y in year_matches if int(y) < self.stale_threshold]

        if stale_years:
            unique_stale = sorted(set(stale_years))
            findings.append(f"Stale year references: {', '.join(str(y) for y in unique_stale)}")

        # Check for "as of" + old date
        as_of = re.findall(r"(?i)as of (\w+ \d{4}|\d{4})", text)
        for match in as_of:
            year_in_match = re.search(r"(20\d{2})", match)
            if year_in_match and int(year_in_match.group()) < self.stale_threshold:
                findings.append(f"Outdated 'as of' reference: {match}")

        total_years = len(set(year_matches)) if year_matches else 1
        stale_ratio = len(set(str(y) for y in stale_years)) / max(total_years, 1)
        score = max(0.0, 1.0 - stale_ratio)

        return CheckResult(
            name=self.name,
            passed=len(findings) == 0,
            score=round(score, 3),
            findings=findings,
            metadata={"years_found": len(set(year_matches)), "stale_years": len(set(str(y) for y in stale_years))},
        )
