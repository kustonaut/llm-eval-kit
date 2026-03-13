"""Validate JSON structure and optional schema compliance in LLM output."""

from __future__ import annotations

import json
import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult


class JSONValidityCheck(Check):
    """Check if LLM output contains valid JSON and optionally validates against a schema.

    Handles:
    - Raw JSON strings
    - JSON embedded in markdown code blocks
    - Multiple JSON objects in output
    - Schema validation (required keys, types)

    Args:
        required_keys: Keys that must exist in the parsed JSON.
        expected_types: Dict mapping key names to expected Python types.
        allow_embedded: If True, extract JSON from markdown code blocks.
    """

    name = "json_validity"

    def __init__(
        self,
        required_keys: list[str] | None = None,
        expected_types: dict[str, type] | None = None,
        allow_embedded: bool = True,
    ) -> None:
        self.required_keys = required_keys or []
        self.expected_types = expected_types or {}
        self.allow_embedded = allow_embedded

    def _extract_json(self, text: str) -> list[str]:
        """Extract JSON strings from text, including markdown code blocks."""
        candidates = []

        # Try markdown code blocks first
        if self.allow_embedded:
            blocks = re.findall(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            candidates.extend(blocks)

        # Try the raw text itself
        candidates.append(text.strip())

        # Try to find JSON objects/arrays in the text
        for match in re.finditer(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])", text):
            candidates.append(match.group())

        return candidates

    def run(self, text: str, **context: Any) -> CheckResult:
        findings: list[str] = []
        parsed = None

        candidates = self._extract_json(text)

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                break
            except (json.JSONDecodeError, ValueError):
                continue

        if parsed is None:
            findings.append("No valid JSON found in output")
            return CheckResult(
                name=self.name, passed=False, score=0.0,
                findings=findings, metadata={"valid_json": False},
            )

        # Check required keys
        if isinstance(parsed, dict):
            missing = [k for k in self.required_keys if k not in parsed]
            if missing:
                findings.append(f"Missing required keys: {', '.join(missing)}")

            # Check expected types
            for key, expected_type in self.expected_types.items():
                if key in parsed and not isinstance(parsed[key], expected_type):
                    actual = type(parsed[key]).__name__
                    findings.append(f"Key '{key}': expected {expected_type.__name__}, got {actual}")

        elif isinstance(parsed, list) and self.required_keys:
            # For arrays, check first element if it's a dict
            if parsed and isinstance(parsed[0], dict):
                missing = [k for k in self.required_keys if k not in parsed[0]]
                if missing:
                    findings.append(f"First element missing keys: {', '.join(missing)}")
            else:
                findings.append("Expected object with required keys, got array of non-objects")

        # Score: 1.0 for valid JSON with all checks passing, degrade for issues
        if not findings:
            score = 1.0
        else:
            score = 0.5  # Valid JSON but schema issues

        return CheckResult(
            name=self.name,
            passed=len(findings) == 0,
            score=score,
            findings=findings,
            metadata={
                "valid_json": True,
                "parsed_type": type(parsed).__name__,
                "keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
            },
        )
