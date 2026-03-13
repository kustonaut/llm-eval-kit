"""Tests for multi-model comparison and reporters."""

from llm_eval_kit.compare import ModelComparator
from llm_eval_kit.scorer import Scorer
from llm_eval_kit.reporters.markdown import MarkdownReporter
from llm_eval_kit.reporters.html import HTMLReporter


def test_compare_two_models():
    comparator = ModelComparator(scorer=Scorer())
    result = comparator.compare(
        prompt="Summarize Q4 results",
        responses={
            "model_a": "Revenue grew 15% in Q4. Cloud services drove growth across all segments. " * 5,
            "model_b": "I'd be happy to help! According to Smith et al., revenue was {{AMOUNT}}. " * 3,
        },
    )
    assert len(result.results) == 2
    assert result.winner == "model_a"  # Clean output should win
    assert len(result.rankings) == 2


def test_compare_table_output():
    comparator = ModelComparator()
    result = comparator.compare(
        prompt="Test",
        responses={
            "good": "A clean professional summary of the quarterly results with clear data points. " * 5,
            "bad": "I'd be happy to help! {{PLACEHOLDER}} [TBD] Lorem ipsum dolor sit amet.",
        },
    )
    table = result.to_table()
    assert "Winner:" in table
    assert "good" in table


def test_compare_to_dict():
    comparator = ModelComparator()
    result = comparator.compare(
        prompt="Test",
        responses={"m1": "Output one. " * 10, "m2": "Output two. " * 10},
    )
    d = result.to_dict()
    assert "winner" in d
    assert "models" in d
    assert len(d["models"]) == 2


def test_compare_batch():
    comparator = ModelComparator()
    results = comparator.compare_batch(
        prompts=["Prompt 1", "Prompt 2"],
        responses={
            "model_a": ["Response A1. " * 10, "Response A2. " * 10],
            "model_b": ["Response B1. " * 10, "Response B2. " * 10],
        },
    )
    assert len(results) == 2


def test_markdown_scorecard_report():
    scorer = Scorer()
    scorecard = scorer.score("A clean output with enough substance for testing. " * 5)
    reporter = MarkdownReporter()
    md = reporter.scorecard_report(scorecard)
    assert "# Eval Report" in md
    assert "Overall Score" in md


def test_markdown_comparison_report():
    comparator = ModelComparator()
    result = comparator.compare(
        prompt="Test", responses={"a": "Output A. " * 10, "b": "Output B. " * 10}
    )
    reporter = MarkdownReporter()
    md = reporter.comparison_report(result)
    assert "# Model Comparison" in md
    assert "Winner" in md


def test_html_scorecard_report():
    scorer = Scorer()
    scorecard = scorer.score("A professional quarterly summary with clear metrics. " * 5)
    reporter = HTMLReporter()
    html = reporter.scorecard_report(scorecard)
    assert "<html" in html
    assert "chart.js" in html.lower() or "Chart" in html
    assert "radarChart" in html
