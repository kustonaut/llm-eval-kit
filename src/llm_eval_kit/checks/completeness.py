"""Check if the output addresses all parts of the input prompt."""

from __future__ import annotations

import re
from typing import Any

from llm_eval_kit.checks.base import Check, CheckResult


class CompletenessCheck(Check):
    """Check if the LLM output addresses all parts of the input prompt.

    Strategies:
    1. Question detection: Finds questions in the prompt and checks if each is addressed
    2. Numbered items: Detects "1. 2. 3." or "a) b) c)" patterns and checks coverage
    3. Keyword coverage: Checks if key nouns from the prompt appear in the output
    4. Explicit requirements: User provides a list of required topics

    Args:
        required_topics: Explicit list of topics/keywords that must appear in output.
        check_questions: Whether to detect and verify questions are answered.
        check_numbered: Whether to detect and verify numbered items are covered.
        min_coverage: Minimum fraction of detected items that must be addressed (0.0-1.0).
    """

    name = "completeness"

    def __init__(
        self,
        required_topics: list[str] | None = None,
        check_questions: bool = True,
        check_numbered: bool = True,
        min_coverage: float = 0.8,
    ) -> None:
        self.required_topics = required_topics or []
        self.check_questions = check_questions
        self.check_numbered = check_numbered
        self.min_coverage = min_coverage

    def _extract_questions(self, text: str) -> list[str]:
        """Extract questions from the prompt."""
        return [q.strip() for q in re.findall(r"[^.!?\n]*\?", text) if len(q.strip()) > 5]

    def _extract_numbered_items(self, text: str) -> list[str]:
        """Extract numbered or lettered list items from the prompt."""
        items = re.findall(r"(?:^|\n)\s*(?:\d+[.)]\s*|[a-z][.)]\s*|-\s*|•\s*)(.+?)(?:\n|$)", text)
        return [item.strip() for item in items if len(item.strip()) > 3]

    def _extract_key_nouns(self, prompt: str) -> list[str]:
        """Extract significant words from prompt (simple heuristic)."""
        # Remove common stop words and short words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "shall", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "about", "like",
            "through", "after", "over", "between", "out", "against", "during",
            "without", "before", "under", "around", "among", "and", "or", "but",
            "not", "no", "nor", "so", "yet", "both", "either", "neither", "each",
            "every", "all", "any", "few", "more", "most", "other", "some", "such",
            "than", "too", "very", "just", "also", "how", "what", "which", "who",
            "whom", "this", "that", "these", "those", "i", "me", "my", "we", "our",
            "you", "your", "he", "him", "his", "she", "her", "it", "its", "they",
            "them", "their", "please", "help", "need", "want", "tell", "give",
            "make", "know", "think", "say", "get", "let", "keep",
        }
        words = re.findall(r"\b[a-zA-Z]{4,}\b", prompt.lower())
        return list(set(w for w in words if w not in stop_words))

    def run(self, text: str, **context: Any) -> CheckResult:
        prompt = context.get("prompt", "")
        findings: list[str] = []
        total_items = 0
        covered_items = 0
        output_lower = text.lower()

        # Check explicit required topics
        if self.required_topics:
            for topic in self.required_topics:
                total_items += 1
                if topic.lower() in output_lower:
                    covered_items += 1
                else:
                    findings.append(f"Missing required topic: '{topic}'")

        # Check questions from prompt
        if self.check_questions and prompt:
            questions = self._extract_questions(prompt)
            for q in questions:
                total_items += 1
                # Check if key words from question appear in output
                key_words = self._extract_key_nouns(q)
                matches = sum(1 for kw in key_words if kw in output_lower)
                if key_words and matches / len(key_words) >= 0.4:
                    covered_items += 1
                else:
                    findings.append(f"Question may be unanswered: '{q[:60]}...'")

        # Check numbered items from prompt
        if self.check_numbered and prompt:
            items = self._extract_numbered_items(prompt)
            for item in items:
                total_items += 1
                key_words = self._extract_key_nouns(item)
                matches = sum(1 for kw in key_words if kw in output_lower)
                if key_words and matches / len(key_words) >= 0.3:
                    covered_items += 1
                else:
                    findings.append(f"Listed item may be missed: '{item[:60]}...'")

        # If no structured items found, fall back to keyword coverage
        if total_items == 0 and prompt:
            key_nouns = self._extract_key_nouns(prompt)
            if key_nouns:
                total_items = len(key_nouns)
                covered_items = sum(1 for kw in key_nouns if kw in output_lower)
                uncovered = [kw for kw in key_nouns if kw not in output_lower]
                if uncovered and len(uncovered) > len(key_nouns) * 0.3:
                    findings.append(f"Prompt keywords not in output: {', '.join(uncovered[:5])}")

        # Calculate score
        if total_items > 0:
            coverage = covered_items / total_items
            score = coverage
        else:
            coverage = 1.0
            score = 1.0

        passed = coverage >= self.min_coverage

        return CheckResult(
            name=self.name,
            passed=passed,
            score=round(score, 3),
            findings=findings,
            metadata={
                "total_items": total_items,
                "covered_items": covered_items,
                "coverage": round(coverage, 3),
            },
        )
