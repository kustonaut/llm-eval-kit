"""Multi-model comparison — run the same prompt through N models and compare scores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from llm_eval_kit.scorer import Scorer, ScoreCard


@dataclass
class ModelResult:
    """Result from a single model in a comparison."""
    model_name: str
    response: str
    scorecard: ScoreCard
    latency_ms: float = 0.0
    cost_usd: float = 0.0


@dataclass
class ComparisonResult:
    """Aggregate results from comparing multiple models."""
    prompt: str
    results: list[ModelResult] = field(default_factory=list)

    @property
    def winner(self) -> str:
        """Model with the highest overall score."""
        if not self.results:
            return "none"
        best = max(self.results, key=lambda r: r.scorecard.overall_score)
        return best.model_name

    @property
    def rankings(self) -> list[tuple[str, float]]:
        """Models ranked by score, descending."""
        return [
            (r.model_name, r.scorecard.overall_score)
            for r in sorted(self.results, key=lambda r: -r.scorecard.overall_score)
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt[:200],
            "winner": self.winner,
            "rankings": self.rankings,
            "models": [
                {
                    "model": r.model_name,
                    "score": r.scorecard.overall_score,
                    "passed": r.scorecard.passed,
                    "checks": {c.name: c.score for c in r.scorecard.checks},
                    "latency_ms": r.latency_ms,
                    "cost_usd": r.cost_usd,
                }
                for r in self.results
            ],
        }

    def to_table(self) -> str:
        """Generate a formatted comparison table."""
        if not self.results:
            return "No results."

        # Header
        check_names = [c.name for c in self.results[0].scorecard.checks]
        header = f"{'Model':<20} {'Overall':>8} {'Pass':>5}"
        for cn in check_names:
            header += f" {cn[:10]:>10}"
        header += f" {'Latency':>10}"

        lines = [header, "-" * len(header)]

        for r in sorted(self.results, key=lambda x: -x.scorecard.overall_score):
            row = f"{r.model_name:<20} {r.scorecard.overall_score:>8.2f} {'✓' if r.scorecard.passed else '✗':>5}"
            for check in r.scorecard.checks:
                row += f" {check.score:>10.2f}"
            row += f" {r.latency_ms:>8.0f}ms"
            lines.append(row)

        lines.append("")
        lines.append(f"Winner: {self.winner}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_table()


class ModelComparator:
    """Compare multiple models on the same prompt(s).

    Usage:
        comparator = ModelComparator(scorer=Scorer())

        # With pre-computed responses
        result = comparator.compare(
            prompt="Summarize Q4...",
            responses={
                "gpt-4o": "Revenue grew 15%...",
                "claude-3": "Q4 saw strong growth...",
                "llama-3": "The quarterly results...",
            },
        )
        print(result)  # Formatted table
        print(result.winner)  # "gpt-4o"

        # With live LLM functions
        result = comparator.compare_live(
            prompt="Summarize Q4...",
            models={
                "gpt-4o": lambda p: openai_call(p, model="gpt-4o"),
                "claude-3": lambda p: anthropic_call(p),
            },
        )
    """

    def __init__(self, scorer: Scorer | None = None) -> None:
        self.scorer = scorer or Scorer()

    def compare(
        self,
        prompt: str,
        responses: dict[str, str],
    ) -> ComparisonResult:
        """Compare pre-computed responses from multiple models.

        Args:
            prompt: The original prompt.
            responses: Dict mapping model_name -> response text.
        """
        results = []
        for model_name, response in responses.items():
            scorecard = self.scorer.score(response, prompt=prompt)
            results.append(ModelResult(
                model_name=model_name,
                response=response,
                scorecard=scorecard,
            ))

        return ComparisonResult(prompt=prompt, results=results)

    def compare_live(
        self,
        prompt: str,
        models: dict[str, Callable[[str], str]],
    ) -> ComparisonResult:
        """Run prompt through live model functions and compare.

        Args:
            prompt: The prompt to send to each model.
            models: Dict mapping model_name -> callable(prompt) -> response.
        """
        import time
        results = []

        for model_name, llm_fn in models.items():
            start = time.perf_counter()
            response = llm_fn(prompt)
            latency = (time.perf_counter() - start) * 1000

            scorecard = self.scorer.score(response, prompt=prompt)
            results.append(ModelResult(
                model_name=model_name,
                response=response,
                scorecard=scorecard,
                latency_ms=round(latency, 1),
            ))

        return ComparisonResult(prompt=prompt, results=results)

    def compare_batch(
        self,
        prompts: list[str],
        responses: dict[str, list[str]],
    ) -> list[ComparisonResult]:
        """Compare multiple models across multiple prompts.

        Args:
            prompts: List of prompts.
            responses: Dict mapping model_name -> list of responses (same order as prompts).
        """
        results = []
        for i, prompt in enumerate(prompts):
            prompt_responses = {
                model: resps[i] for model, resps in responses.items()
                if i < len(resps)
            }
            results.append(self.compare(prompt=prompt, responses=prompt_responses))
        return results
