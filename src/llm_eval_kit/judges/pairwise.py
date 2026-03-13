"""Pairwise comparison judge — compare two outputs, pick the better one."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import re


@dataclass
class PairwiseResult:
    """Result from a pairwise comparison."""
    winner: str  # "A", "B", or "tie"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    raw_response: str


_PAIRWISE_PROMPT = """You are an expert evaluator. Compare two LLM outputs for the same prompt.

## Evaluation Criteria
{criteria}

## Original Prompt
{prompt}

## Output A
{output_a}

## Output B
{output_b}

## Instructions
1. Carefully compare both outputs against the criteria.
2. Consider: accuracy, completeness, clarity, and relevance.
3. Choose the better output.

Respond in this exact format:
REASONING: <your step-by-step comparison>
WINNER: <A or B or TIE>
CONFIDENCE: <HIGH or MEDIUM or LOW>"""


class PairwiseJudge:
    """Compare two LLM outputs and determine which is better.

    Useful when absolute scoring is hard but relative comparison is easy
    (e.g., "which summary is more informative?").

    Usage:
        judge = PairwiseJudge(llm_fn=my_llm_function)
        result = judge.compare(
            output_a="Summary version 1...",
            output_b="Summary version 2...",
            prompt="Summarize Q4 results",
            criteria="Which summary is more informative and concise?",
        )
        print(result.winner, result.confidence, result.reasoning)

    Args:
        llm_fn: Function that takes a prompt string and returns a response string.
    """

    def __init__(self, llm_fn: Callable[[str], str] | None = None) -> None:
        self.llm_fn = llm_fn

    def compare(
        self,
        output_a: str,
        output_b: str,
        prompt: str = "",
        criteria: str = "Which output is better in terms of accuracy, completeness, and clarity?",
    ) -> PairwiseResult:
        """Compare two outputs and pick the better one.

        Args:
            output_a: First LLM output.
            output_b: Second LLM output.
            prompt: The original input prompt.
            criteria: Comparison criteria.

        Returns:
            PairwiseResult with winner, confidence, and reasoning.
        """
        if not self.llm_fn:
            raise ValueError("No LLM function provided. Pass llm_fn to the constructor.")

        eval_prompt = _PAIRWISE_PROMPT.format(
            criteria=criteria, prompt=prompt,
            output_a=output_a, output_b=output_b,
        )

        raw_response = self.llm_fn(eval_prompt)
        winner, confidence, reasoning = self._parse_response(raw_response)

        return PairwiseResult(
            winner=winner,
            confidence=confidence,
            reasoning=reasoning,
            raw_response=raw_response,
        )

    @staticmethod
    def _parse_response(response: str) -> tuple[str, float, str]:
        """Parse WINNER, CONFIDENCE, and REASONING from response."""
        reasoning = ""
        winner = "tie"
        confidence = 0.5

        reasoning_match = re.search(r"REASONING:\s*(.+?)(?=WINNER:|$)", response, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        winner_match = re.search(r"WINNER:\s*(A|B|TIE)", response, re.IGNORECASE)
        if winner_match:
            winner = winner_match.group(1).upper()
            if winner == "TIE":
                winner = "tie"

        confidence_match = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", response, re.IGNORECASE)
        if confidence_match:
            conf_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}
            confidence = conf_map.get(confidence_match.group(1).upper(), 0.5)

        return winner, confidence, reasoning
