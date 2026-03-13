"""Tests for the eval runner."""

from llm_eval_kit.eval_runner import EvalRunner, TestCase, SuiteResult
from llm_eval_kit.scorer import Scorer


def test_run_with_precomputed_responses():
    runner = EvalRunner(scorer=Scorer())
    cases = [
        TestCase(
            name="good_summary",
            prompt="Summarize Q4 results",
            expected_keywords=["revenue", "growth"],
        ),
    ]
    responses = {
        "good_summary": "Revenue grew 15% in Q4. The growth was driven by cloud services. "
                        "Operating income increased year over year with strong margins. " * 3,
    }
    result = runner.run(cases, suite_name="test", responses=responses)
    assert result.total == 1
    assert result.results[0].keyword_pass


def test_missing_keywords_flagged():
    runner = EvalRunner(scorer=Scorer())
    cases = [
        TestCase(
            name="missing_kw",
            prompt="Talk about cats",
            expected_keywords=["feline", "whiskers"],
        ),
    ]
    responses = {"missing_kw": "Dogs are great pets. They are loyal and friendly. " * 5}
    result = runner.run(cases, responses=responses)
    assert not result.results[0].keyword_pass
    assert "Missing keywords" in result.results[0].findings[0]


def test_banned_keywords_flagged():
    runner = EvalRunner(scorer=Scorer())
    cases = [
        TestCase(
            name="banned_kw",
            prompt="Write professionally",
            banned_keywords=["I think", "maybe"],
        ),
    ]
    responses = {"banned_kw": "I think maybe we should consider this approach carefully. " * 5}
    result = runner.run(cases, responses=responses)
    assert not result.results[0].banned_pass


def test_regression_detection():
    baseline = SuiteResult(name="baseline")
    from llm_eval_kit.eval_runner import TestResult
    from llm_eval_kit.scorer import ScoreCard
    baseline.results = [
        TestResult(
            test_case=TestCase(name="test_1", prompt=""),
            response="",
            scorecard=ScoreCard(overall_score=0.9, passed=True),
            overall_pass=True,
        ),
    ]

    current = SuiteResult(name="current")
    current.results = [
        TestResult(
            test_case=TestCase(name="test_1", prompt=""),
            response="",
            scorecard=ScoreCard(overall_score=0.3, passed=False),
            overall_pass=False,
        ),
    ]

    regressions = current.regressions(baseline)
    assert regressions == ["test_1"]


def test_pass_rate():
    result = SuiteResult(name="test")
    assert result.pass_rate == 0.0
    assert result.avg_score == 0.0
