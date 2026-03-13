"""G-Eval style LLM-as-Judge — custom criteria, chain-of-thought, scored evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from llm_eval_kit.checks.base import CheckResult


@dataclass
class JudgeResult:
    """Result from an LLM judge evaluation."""
    score: float  # 0.0 to 1.0
    reasoning: str
    raw_response: str
    metadata: dict[str, Any]


_GEVAL_PROMPT = """You are an expert evaluator. Score the following LLM output based on the criteria below.

## Criteria
{criteria}

## Input/Prompt
{prompt}

## LLM Output
{output}

## Instructions
1. Think step by step about how well the output meets the criteria.
2. Provide your reasoning.
3. Give a score from 1 to 5:
   1 = Completely fails the criteria
   2 = Mostly fails with minor positives
   3 = Partially meets criteria
   4 = Mostly meets criteria with minor issues
   5 = Fully meets criteria

Respond in this exact format:
REASONING: <your step-by-step reasoning>
SCORE: <1-5>"""


_REFERENCE_PROMPT = """You are an expert evaluator. Compare the LLM output against the reference answer.

## Criteria
{criteria}

## Input/Prompt
{prompt}

## Reference Answer
{reference}

## LLM Output
{output}

## Instructions
1. Compare the output to the reference answer.
2. Consider: accuracy, completeness, and relevance.
3. Give a score from 1 to 5:
   1 = Completely wrong or irrelevant
   2 = Major errors or omissions
   3 = Partially correct
   4 = Mostly correct with minor differences
   5 = Matches or exceeds reference quality

Respond in this exact format:
REASONING: <your comparison reasoning>
SCORE: <1-5>"""


class LLMJudge:
    """G-Eval style LLM judge — evaluates output against custom criteria.

    Uses chain-of-thought reasoning to produce a 1-5 score, normalized to 0.0-1.0.

    Usage:
        # With OpenAI
        import openai
        def call_llm(prompt: str) -> str:
            return openai.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

        judge = LLMJudge(llm_fn=call_llm)
        result = judge.evaluate(
            output="The quarterly revenue was $50B...",
            criteria="Is the output factually accurate and well-structured?",
            prompt="Summarize Q4 results",
        )
        print(result.score, result.reasoning)

    Args:
        llm_fn: Function that takes a prompt string and returns a response string.
        criteria: Default evaluation criteria (can be overridden per call).
    """

    def __init__(
        self,
        llm_fn: Callable[[str], str] | None = None,
        criteria: str = "Is the output accurate, complete, and well-structured?",
    ) -> None:
        self.llm_fn = llm_fn
        self.default_criteria = criteria

    def evaluate(
        self,
        output: str,
        criteria: str | None = None,
        prompt: str = "",
        reference: str | None = None,
        **kwargs: Any,
    ) -> JudgeResult:
        """Evaluate an LLM output using G-Eval style chain-of-thought scoring.

        Args:
            output: The LLM output to evaluate.
            criteria: Evaluation criteria (defaults to constructor value).
            prompt: The original prompt/input.
            reference: Optional reference answer for comparison.

        Returns:
            JudgeResult with score (0.0-1.0), reasoning, and raw response.
        """
        if not self.llm_fn:
            raise ValueError(
                "No LLM function provided. Pass llm_fn to the constructor.\n"
                "Example: LLMJudge(llm_fn=lambda p: openai.chat(...))"
            )

        criteria = criteria or self.default_criteria

        if reference:
            eval_prompt = _REFERENCE_PROMPT.format(
                criteria=criteria, prompt=prompt, reference=reference, output=output,
            )
        else:
            eval_prompt = _GEVAL_PROMPT.format(
                criteria=criteria, prompt=prompt, output=output,
            )

        raw_response = self.llm_fn(eval_prompt)
        score, reasoning = self._parse_response(raw_response)

        return JudgeResult(
            score=score,
            reasoning=reasoning,
            raw_response=raw_response,
            metadata={"criteria": criteria, "has_reference": reference is not None},
        )

    def as_check(
        self,
        name: str = "llm_judge",
        criteria: str | None = None,
        threshold: float = 0.6,
    ) -> _JudgeCheck:
        """Convert this judge into a Check that can be used with Scorer.

        Args:
            name: Name for the check.
            criteria: Override criteria for this check.
            threshold: Score threshold for pass/fail.
        """
        return _JudgeCheck(
            judge=self,
            check_name=name,
            criteria=criteria or self.default_criteria,
            threshold=threshold,
        )

    @staticmethod
    def _parse_response(response: str) -> tuple[float, str]:
        """Parse REASONING and SCORE from the judge's response."""
        import re

        reasoning = ""
        score = 0.5

        # Extract reasoning
        reasoning_match = re.search(r"REASONING:\s*(.+?)(?=SCORE:|$)", response, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        # Extract score
        score_match = re.search(r"SCORE:\s*(\d(?:\.\d)?)", response, re.IGNORECASE)
        if score_match:
            raw_score = float(score_match.group(1))
            score = (raw_score - 1) / 4  # Normalize 1-5 to 0.0-1.0
            score = max(0.0, min(1.0, score))

        return score, reasoning


class _JudgeCheck:
    """Adapter that wraps an LLMJudge as a Check for use in Scorer."""

    def __init__(self, judge: LLMJudge, check_name: str, criteria: str, threshold: float) -> None:
        self.name = check_name
        self.judge = judge
        self.criteria = criteria
        self.threshold = threshold

    def run(self, text: str, **context: Any) -> CheckResult:
        prompt = context.get("prompt", "")
        reference = context.get("reference")

        try:
            result = self.judge.evaluate(
                output=text, criteria=self.criteria,
                prompt=prompt, reference=reference,
            )
            return CheckResult(
                name=self.name,
                passed=result.score >= self.threshold,
                score=result.score,
                findings=[result.reasoning] if result.reasoning else [],
                metadata=result.metadata,
            )
        except Exception as e:
            return CheckResult(
                name=self.name, passed=False, score=0.0,
                findings=[f"Judge error: {e}"], metadata={"error": str(e)},
            )
