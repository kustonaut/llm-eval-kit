# Contributing to LLM Eval Kit

Contributions welcome! Here's how to get started.

## Setup

```bash
git clone https://github.com/kustonaut/llm-eval-kit.git
cd llm-eval-kit
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest --tb=short -q
```

## Linting

```bash
ruff check src/ tests/
mypy src/llm_eval_kit/ --ignore-missing-imports
```

## Adding a Custom Check

1. Create a file in `src/llm_eval_kit/checks/`
2. Subclass `Check` and implement `run()`:

```python
from llm_eval_kit.checks.base import Check, CheckResult

class MyCheck(Check):
    name = "my_check"

    def run(self, text: str, **context) -> CheckResult:
        issues = []
        if "bad_word" in text.lower():
            issues.append("Contains bad_word")
        score = 0.0 if issues else 1.0
        return CheckResult(name=self.name, passed=not issues, score=score, findings=issues)
```

3. Register it in `checks/__init__.py`
4. Add tests in `tests/`

## Pull Requests

- One feature per PR
- Tests required for new checks
- Run `ruff check` and `mypy` before submitting
