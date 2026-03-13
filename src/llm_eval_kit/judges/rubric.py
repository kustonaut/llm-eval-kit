"""Rubric-based judge — score output against a structured rubric with defined levels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import re


@dataclass
class RubricLevel:
    """A single level in a scoring rubric."""
    score: int  # 1-5
    label: str
    description: str


@dataclass
class RubricResult:
    """Result from rubric-based evaluation."""
    score: float  # 0.0 to 1.0 (normalized)
    raw_score: int  # 1-5
    level_label: str
    reasoning: str
    raw_response: str


_DEFAULT_RUBRIC = [
    RubricLevel(1, "Poor", "Output is irrelevant, incorrect, or incoherent."),
    RubricLevel(2, "Below Average", "Output addresses the prompt but has significant errors or omissions."),
    RubricLevel(3, "Average", "Output partially addresses the prompt with some accuracy."),
    RubricLevel(4, "Good", "Output is mostly accurate, complete, and well-structured."),
    RubricLevel(5, "Excellent", "Output fully addresses the prompt — accurate, complete, clear, and concise."),
]


_RUBRIC_PROMPT = """You are an expert evaluator. Score the LLM output using the rubric below.

## Evaluation Criteria
{criteria}

## Rubric
{rubric_text}

## Input/Prompt
{prompt}

## LLM Output
{output}

## Instructions
1. Read the output carefully.
2. Match it to the most appropriate rubric level.
3. Explain your reasoning.

Respond in this exact format:
REASONING: <your reasoning>
LEVEL: <1-5>"""


class RubricJudge:
    """Score LLM output against a structured rubric with defined quality levels.

    More interpretable than free-form G-Eval — each score level has a clear definition.

    Usage:
        judge = RubricJudge(llm_fn=my_llm)

        # Use default rubric
        result = judge.evaluate(
            output="...",
            prompt="...",
            criteria="Evaluate the clarity and accuracy of this summary.",
        )

        # Use custom rubric
        rubric = [
            RubricLevel(1, "Wrong", "Contains factual errors"),
            RubricLevel(2, "Incomplete", "Missing key information"),
            RubricLevel(3, "Adequate", "Covers basics but lacks depth"),
            RubricLevel(4, "Good", "Accurate and reasonably complete"),
            RubricLevel(5, "Excellent", "Comprehensive, accurate, well-written"),
        ]
        result = judge.evaluate(output="...", rubric=rubric)

    Args:
        llm_fn: Function that takes a prompt string and returns a response string.
        rubric: Default rubric levels (can be overridden per call).
        criteria: Default evaluation criteria.
    """

    def __init__(
        self,
        llm_fn: Callable[[str], str] | None = None,
        rubric: list[RubricLevel] | None = None,
        criteria: str = "Evaluate the quality of this output.",
    ) -> None:
        self.llm_fn = llm_fn
        self.default_rubric = rubric or list(_DEFAULT_RUBRIC)
        self.default_criteria = criteria

    def evaluate(
        self,
        output: str,
        prompt: str = "",
        criteria: str | None = None,
        rubric: list[RubricLevel] | None = None,
    ) -> RubricResult:
        """Evaluate output against the rubric.

        Args:
            output: The LLM output to evaluate.
            prompt: The original input prompt.
            criteria: Evaluation criteria (overrides default).
            rubric: Rubric levels (overrides default).
        """
        if not self.llm_fn:
            raise ValueError("No LLM function provided. Pass llm_fn to the constructor.")

        rubric = rubric or self.default_rubric
        criteria = criteria or self.default_criteria

        rubric_text = "\n".join(
            f"  {level.score} — {level.label}: {level.description}"
            for level in sorted(rubric, key=lambda l: l.score)
        )

        eval_prompt = _RUBRIC_PROMPT.format(
            criteria=criteria, rubric_text=rubric_text,
            prompt=prompt, output=output,
        )

        raw_response = self.llm_fn(eval_prompt)
        raw_score, reasoning = self._parse_response(raw_response)

        # Find matching level
        level_label = "Unknown"
        for level in rubric:
            if level.score == raw_score:
                level_label = level.label
                break

        # Normalize to 0.0-1.0
        min_score = min(l.score for l in rubric)
        max_score = max(l.score for l in rubric)
        normalized = (raw_score - min_score) / max(max_score - min_score, 1)

        return RubricResult(
            score=round(normalized, 3),
            raw_score=raw_score,
            level_label=level_label,
            reasoning=reasoning,
            raw_response=raw_response,
        )

    @staticmethod
    def _parse_response(response: str) -> tuple[int, str]:
        """Parse LEVEL and REASONING from response."""
        reasoning = ""
        score = 3

        reasoning_match = re.search(r"REASONING:\s*(.+?)(?=LEVEL:|$)", response, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        level_match = re.search(r"LEVEL:\s*(\d)", response, re.IGNORECASE)
        if level_match:
            score = int(level_match.group(1))
            score = max(1, min(5, score))

        return score, reasoning
