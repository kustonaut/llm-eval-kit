"""Tests for all new checks: PII, toxicity, JSON, completeness, consistency."""

from llm_eval_kit.checks.pii import PIICheck
from llm_eval_kit.checks.toxicity import ToxicityCheck
from llm_eval_kit.checks.json_validity import JSONValidityCheck
from llm_eval_kit.checks.completeness import CompletenessCheck
from llm_eval_kit.checks.consistency import ConsistencyCheck


# ── PII Check ──

def test_pii_detects_email():
    check = PIICheck()
    result = check.run("Contact john.doe@company.com for details.")
    assert not result.passed
    assert any("Email" in f for f in result.findings)


def test_pii_detects_ssn():
    check = PIICheck()
    result = check.run("SSN: 123-45-6789 is on file.")
    assert not result.passed
    assert any("SSN" in f for f in result.findings)


def test_pii_detects_api_key():
    check = PIICheck()
    result = check.run("Use sk-abc123def456ghi789jkl012mno345pqr678stu to authenticate.")
    assert not result.passed


def test_pii_allows_example_emails():
    check = PIICheck()
    result = check.run("Send to example@example.com for testing.")
    assert result.passed


def test_pii_clean_text():
    check = PIICheck()
    result = check.run("Revenue grew 15% in Q4, driven by cloud expansion across all regions.")
    assert result.passed
    assert result.score == 1.0


# ── Toxicity Check ──

def test_toxicity_detects_insult():
    check = ToxicityCheck()
    result = check.run("That idea is stupid and you are an idiot for suggesting it.")
    assert not result.passed
    assert result.metadata["worst_severity"] == "moderate"


def test_toxicity_clean_text():
    check = ToxicityCheck()
    result = check.run("This is a well-reasoned and thoughtful analysis of the market conditions.")
    assert result.passed
    assert result.score == 1.0


def test_toxicity_mild_profanity_ignored_by_default():
    check = ToxicityCheck(include_mild=False)
    result = check.run("What the hell happened to the quarterly numbers?")
    assert result.passed  # Mild not included by default


def test_toxicity_mild_profanity_flagged_when_enabled():
    check = ToxicityCheck(include_mild=True)
    result = check.run("What the hell happened to the quarterly numbers?")
    assert result.score < 1.0  # Score should be reduced
    assert result.metadata["worst_severity"] == "mild"
    assert len(result.findings) >= 1


# ── JSON Validity Check ──

def test_json_valid_object():
    check = JSONValidityCheck()
    result = check.run('{"name": "Alice", "age": 30}')
    assert result.passed
    assert result.score == 1.0


def test_json_valid_in_code_block():
    check = JSONValidityCheck()
    result = check.run('Here is the result:\n```json\n{"status": "ok"}\n```\nDone.')
    assert result.passed


def test_json_invalid():
    check = JSONValidityCheck()
    result = check.run("This is not JSON at all, just plain text.")
    assert not result.passed
    assert result.score == 0.0


def test_json_required_keys():
    check = JSONValidityCheck(required_keys=["name", "email"])
    result = check.run('{"name": "Alice"}')
    assert not result.passed
    assert any("Missing" in f for f in result.findings)


def test_json_type_check():
    check = JSONValidityCheck(expected_types={"age": int})
    result = check.run('{"age": "thirty"}')
    assert not result.passed
    assert any("expected int" in f for f in result.findings)


# ── Completeness Check ──

def test_completeness_with_required_topics():
    check = CompletenessCheck(required_topics=["revenue", "growth", "outlook"])
    result = check.run("Revenue grew 15%. The growth trajectory is strong. The outlook for next quarter is positive.")
    assert result.passed


def test_completeness_missing_topic():
    check = CompletenessCheck(required_topics=["revenue", "growth", "risks"])
    result = check.run("Revenue grew 15%. Growth was strong across all segments.")
    assert not result.passed
    assert any("risks" in f.lower() for f in result.findings)


def test_completeness_questions_from_prompt():
    check = CompletenessCheck(required_topics=["price", "shipping"])
    result = check.run(
        "The price is $49.99. Shipping takes 3-5 business days.",
    )
    assert result.passed
    assert result.score >= 0.8


def test_completeness_no_prompt():
    check = CompletenessCheck()
    result = check.run("A reasonable summary of the quarterly performance.")
    assert result.passed  # No prompt = nothing to check against


# ── Consistency Check ──

def test_consistency_numerical_contradiction():
    check = ConsistencyCheck()
    result = check.run("Revenue increased to $50 billion. Later analysis shows revenue was $45 billion.")
    assert not result.passed
    assert any("Different values" in f for f in result.findings)


def test_consistency_clean_text():
    check = ConsistencyCheck()
    result = check.run(
        "Revenue grew 15% year over year. The growth was primarily driven by "
        "cloud services, which now represent 40% of total revenue."
    )
    assert result.passed


def test_consistency_explicit_contradiction_signal():
    check = ConsistencyCheck()
    result = check.run("This contradicts the earlier statement about market conditions.")
    assert not result.passed
