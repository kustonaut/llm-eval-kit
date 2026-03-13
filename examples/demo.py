"""Quick demo — score text and run an eval suite."""

from llm_eval_kit import Scorer, EvalRunner
from llm_eval_kit.checks import HallucinationCheck, PlaceholderCheck, StyleCheck

# ── 1. Score a single output ──
scorer = Scorer()

good_output = """
Revenue grew 15% in Q4, driven by cloud services expansion.
Cloud platform revenue increased 29% year over year. SaaS subscribers
reached 78.4 million. Operating income grew 20% across all segments.
"""

bad_output = """
I'd be happy to help! According to Smith et al. (2019), revenue was
approximately {{REVENUE_AMOUNT}}. In today's world, it's worth noting
that [TBD] metrics showed improvement. Please verify this with sources.
I hope this helps! Feel free to ask more questions.
"""

print("=" * 50)
print("GOOD OUTPUT:")
print(scorer.score(good_output))
print()
print("BAD OUTPUT:")
print(scorer.score(bad_output))

# ── 2. Run an eval suite ──
from llm_eval_kit.eval_runner import TestCase

cases = [
    TestCase(
        name="revenue_summary",
        prompt="Summarize Q4 revenue",
        expected_keywords=["revenue", "growth"],
        banned_keywords=["I think", "maybe"],
        min_score=0.7,
    ),
    TestCase(
        name="action_items",
        prompt="List action items from the meeting",
        expected_keywords=["action", "owner"],
        min_score=0.7,
    ),
]

responses = {
    "revenue_summary": good_output,
    "action_items": "Action items: (1) Akshay reviews the doc by Friday. "
                    "Owner: Akshay. Deadline: March 15. "
                    "The team agreed to reconvene next week. " * 3,
}

runner = EvalRunner(scorer=scorer)
result = runner.run(cases, suite_name="demo", responses=responses)

print()
print("=" * 50)
print("EVAL SUITE RESULTS:")
print(result)
