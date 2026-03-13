"""Golden test case runner — define expected outputs, detect regressions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from llm_eval_kit.scorer import Scorer, ScoreCard


@dataclass
class TestCase:
    """A single golden test case."""

    name: str
    prompt: str
    expected_keywords: list[str] = field(default_factory=list)
    banned_keywords: list[str] = field(default_factory=list)
    min_score: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of running a single test case."""

    test_case: TestCase
    response: str
    scorecard: ScoreCard
    keyword_pass: bool = True
    banned_pass: bool = True
    overall_pass: bool = True
    findings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "PASS" if self.overall_pass else "FAIL"
        return f"[{status}] {self.test_case.name}: score={self.scorecard.overall_score:.2f}, keywords={self.keyword_pass}, banned={self.banned_pass}"


@dataclass
class SuiteResult:
    """Aggregate results from running an eval suite."""

    name: str
    results: list[TestResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.overall_pass)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return self.passed / max(self.total, 1)

    @property
    def avg_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.scorecard.overall_score for r in self.results) / len(self.results)

    def regressions(self, baseline: SuiteResult | None) -> list[str]:
        """Compare against a baseline run. Return test names that regressed."""
        if not baseline:
            return []
        baseline_map = {r.test_case.name: r for r in baseline.results}
        regressions = []
        for r in self.results:
            base = baseline_map.get(r.test_case.name)
            if base and base.overall_pass and not r.overall_pass:
                regressions.append(r.test_case.name)
        return regressions

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.name,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 3),
            "avg_score": round(self.avg_score, 3),
            "results": [
                {
                    "name": r.test_case.name,
                    "passed": r.overall_pass,
                    "score": r.scorecard.overall_score,
                    "findings": r.findings,
                }
                for r in self.results
            ],
        }

    def __str__(self) -> str:
        lines = [
            f"Suite: {self.name} — {self.passed}/{self.total} passed ({self.pass_rate:.0%}), avg score: {self.avg_score:.2f}",
        ]
        for r in self.results:
            lines.append(f"  {r}")
        return "\n".join(lines)


class EvalRunner:
    """Run golden test suites against an LLM function and detect regressions.

    Usage:
        def my_llm(prompt: str) -> str:
            return openai.chat(prompt)

        runner = EvalRunner(llm_fn=my_llm)
        suite = runner.load_suite("tests/eval_suite.yaml")
        result = runner.run(suite)
        print(result)

        # Regression detection:
        regressions = result.regressions(previous_result)
    """

    def __init__(
        self,
        llm_fn: Callable[[str], str] | None = None,
        scorer: Scorer | None = None,
    ) -> None:
        self.llm_fn = llm_fn
        self.scorer = scorer or Scorer()

    def load_suite(self, path: str | Path) -> tuple[str, list[TestCase]]:
        """Load test cases from a YAML or JSON file.

        Expected format:
            name: "My Eval Suite"
            cases:
              - name: "basic_test"
                prompt: "Summarize this..."
                expected_keywords: ["summary", "key points"]
                banned_keywords: ["I think", "maybe"]
                min_score: 0.7
        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        suite_name = data.get("name", path.stem)
        cases = []
        for c in data.get("cases", []):
            cases.append(TestCase(
                name=c["name"],
                prompt=c.get("prompt", ""),
                expected_keywords=c.get("expected_keywords", []),
                banned_keywords=c.get("banned_keywords", []),
                min_score=c.get("min_score", 0.7),
                metadata=c.get("metadata", {}),
            ))
        return suite_name, cases

    def run(
        self,
        cases: list[TestCase],
        suite_name: str = "default",
        responses: dict[str, str] | None = None,
    ) -> SuiteResult:
        """Run all test cases and return aggregate results.

        Args:
            cases: List of test cases to run.
            suite_name: Name for the suite result.
            responses: Pre-computed responses keyed by test case name.
                       If not provided, uses llm_fn to generate responses.
        """
        results: list[TestResult] = []

        for tc in cases:
            # Get response
            if responses and tc.name in responses:
                response = responses[tc.name]
            elif self.llm_fn:
                response = self.llm_fn(tc.prompt)
            else:
                response = ""

            # Score
            scorecard = self.scorer.score(response, prompt=tc.prompt)
            findings: list[str] = []

            # Keyword checks
            response_lower = response.lower()
            missing_keywords = [k for k in tc.expected_keywords if k.lower() not in response_lower]
            keyword_pass = len(missing_keywords) == 0
            if missing_keywords:
                findings.append(f"Missing keywords: {', '.join(missing_keywords)}")

            found_banned = [k for k in tc.banned_keywords if k.lower() in response_lower]
            banned_pass = len(found_banned) == 0
            if found_banned:
                findings.append(f"Banned keywords found: {', '.join(found_banned)}")

            # Add check-level findings
            for check in scorecard.failed_checks:
                findings.extend(check.findings[:3])

            overall_pass = (
                scorecard.overall_score >= tc.min_score
                and keyword_pass
                and banned_pass
            )

            results.append(TestResult(
                test_case=tc,
                response=response,
                scorecard=scorecard,
                keyword_pass=keyword_pass,
                banned_pass=banned_pass,
                overall_pass=overall_pass,
                findings=findings,
            ))

        return SuiteResult(name=suite_name, results=results)

    def save_result(self, result: SuiteResult, path: str | Path) -> None:
        """Save suite result to JSON for baseline comparison."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

    def load_baseline(self, path: str | Path) -> SuiteResult | None:
        """Load a previous suite result for regression comparison."""
        path = Path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Reconstruct minimal SuiteResult for regression checking
        results = []
        for r in data.get("results", []):
            tc = TestCase(name=r["name"], prompt="")
            sc = ScoreCard(overall_score=r.get("score", 0.0), passed=r.get("passed", False))
            results.append(TestResult(
                test_case=tc,
                response="",
                scorecard=sc,
                overall_pass=r.get("passed", False),
            ))
        return SuiteResult(name=data.get("suite", "baseline"), results=results)
