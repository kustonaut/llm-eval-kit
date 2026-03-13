"""Tests for the scoring engine."""

from llm_eval_kit.scorer import Scorer


def test_clean_text_passes():
    scorer = Scorer(threshold=0.6)
    result = scorer.score(
        "The quarterly revenue increased by 15% driven by growth in cloud services. "
        "Cloud platform revenue grew 29% year over year. SaaS subscribers "
        "reached 78.4 million in 2026."
    )
    assert result.passed
    assert result.overall_score >= 0.6


def test_placeholder_text_fails():
    scorer = Scorer()
    result = scorer.score("The report shows {{METRIC_VALUE}} for [TBD] quarter.")
    placeholder_check = next(c for c in result.checks if c.name == "placeholder")
    assert not placeholder_check.passed
    assert len(placeholder_check.findings) >= 2


def test_ai_tells_detected():
    scorer = Scorer()
    result = scorer.score(
        "I'd be happy to help you with that! Certainly, let me delve into the "
        "landscape of this topic. Great question! In today's world, it's worth "
        "noting that this is quite important. I hope this helps!"
    )
    style_check = next(c for c in result.checks if c.name == "style")
    assert not style_check.passed
    assert len(style_check.findings) >= 4


def test_hallucination_markers_detected():
    scorer = Scorer()
    result = scorer.score(
        "According to Smith et al., 2019, the results show improvement. "
        "I'm not sure about the exact numbers. Please verify this with "
        "the original source. Based on my knowledge cutoff, this may "
        "have changed since then."
    )
    hallucination_check = next(c for c in result.checks if c.name == "hallucination")
    assert not hallucination_check.passed
    assert len(hallucination_check.findings) >= 2


def test_empty_text_fails_length():
    scorer = Scorer()
    result = scorer.score("Short.")
    length_check = next(c for c in result.checks if c.name == "length")
    assert not length_check.passed


def test_custom_threshold():
    scorer = Scorer(threshold=0.9)
    result = scorer.score("A reasonable output with enough words to pass the length check. " * 5)
    # With strict threshold, minor issues may cause failure
    assert result.threshold == 0.9


def test_scorecard_summary():
    scorer = Scorer()
    result = scorer.score("A clean and professional summary of the project status in 2026. " * 5)
    assert result.total_checks == 5
    assert result.passed_checks >= 0
    assert 0.0 <= result.overall_score <= 1.0
