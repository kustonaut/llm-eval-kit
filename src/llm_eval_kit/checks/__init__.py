"""Pluggable quality checks for LLM outputs."""

from llm_eval_kit.checks.base import Check, CheckResult
from llm_eval_kit.checks.hallucination import HallucinationCheck
from llm_eval_kit.checks.placeholder import PlaceholderCheck
from llm_eval_kit.checks.style import StyleCheck
from llm_eval_kit.checks.freshness import FreshnessCheck
from llm_eval_kit.checks.length import LengthCheck

__all__ = [
    "Check",
    "CheckResult",
    "HallucinationCheck",
    "PlaceholderCheck",
    "StyleCheck",
    "FreshnessCheck",
    "LengthCheck",
]
