<div align="center">

```
██╗     ██╗     ███╗   ███╗
██║     ██║     ████╗ ████║
██║     ██║     ██╔████╔██║
██║     ██║     ██║╚██╔╝██║
███████╗███████╗██║ ╚═╝ ██║
╚══════╝╚══════╝╚═╝     ╚═╝
███████╗██╗   ██╗ █████╗ ██╗         ██╗  ██╗██╗████████╗
██╔════╝██║   ██║██╔══██╗██║         ██║ ██╔╝██║╚══██╔══╝
█████╗  ██║   ██║███████║██║         █████╔╝ ██║   ██║
██╔══╝  ╚██╗ ██╔╝██╔══██║██║         ██╔═██╗ ██║   ██║
███████╗ ╚████╔╝ ██║  ██║███████╗    ██║  ██╗██║   ██║
╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝   ╚═╝
```

# LLM Eval Kit 🧪

[![CI](https://github.com/kustonaut/llm-eval-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/kustonaut/llm-eval-kit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/llm-eval-kit.svg)](https://pypi.org/project/llm-eval-kit/)
[![Demo](https://img.shields.io/badge/demo-live-ff6ec7.svg)](https://kustonaut.github.io/llm-eval-kit)

**Stop shipping vibes. Start shipping quality.**

10 quality checks, LLM-as-judge, multi-model comparison, and regression detection for LLM outputs.
Zero API keys required for rule-based scoring. Bring your own LLM for judge-based evaluation.

[**🎮 Live Demo**](https://kustonaut.github.io/llm-eval-kit) · [**📦 PyPI**](https://pypi.org/project/llm-eval-kit/) · [**🤝 Contributing**](CONTRIBUTING.md)

</div>

---

## The Problem

You changed a prompt. Did the output get better or worse?

```
Before:  "Summarize Q4 results"  →  Clean, factual 200-word summary
After:   "Summarize Q4 results"  →  "I'd be happy to help! According to Smith et al..."

What happened?  ¯\_(ツ)_/¯
```

Most teams evaluate LLM output by reading it. That doesn't scale. It doesn't catch regressions. It doesn't measure quality over time.

**LLM Eval Kit brings testing discipline to AI workflows.**

---

## Features

| | Feature | What It Does |
|---|---------|-------------|
| 🎯 | **10 Quality Checks** | Hallucination, placeholder, style, freshness, length, PII, toxicity, JSON validity, completeness, consistency |
| 🧑‍⚖️ | **LLM-as-Judge** | G-Eval style scoring, pairwise comparison, rubric-based grading (OpenAI, Anthropic, local models) |
| 🔄 | **Multi-Model Comparison** | Run same prompt through N models, ranked table with per-check breakdown |
| 📉 | **Regression Detection** | Compare runs against baselines — catch quality drops before users do |
| 📊 | **HTML + Markdown Reports** | Dark-themed reports with Chart.js radar/bar charts |
| 🧪 | **Golden Test Suites** | Define expected keywords, banned phrases, min scores in YAML |
| 📝 | **Call Logging** | JSONL logger with prompt, response, model, latency, tokens, cost |
| 🔌 | **Pluggable** | Add custom checks in 10 lines — subclass `Check`, implement `run()` |
| ⚙️ | **CLI** | `llm-eval score`, `llm-eval eval`, `llm-eval costs` |
| 🔒 | **Zero-Dep Scoring** | Rule-based checks need zero API keys. LLM judge is opt-in. |

---

## Quick Start

```bash
pip install llm-eval-kit
```

### Score a single output

```python
from llm_eval_kit import Scorer

scorer = Scorer()
result = scorer.score("""
Revenue grew 15% in Q4, driven by cloud services.
Cloud platform revenue increased 29% year over year.
""")
print(result)
# ScoreCard: 0.95 [PASS] (5/5 checks passed)
#   [PASS] hallucination: 1.00
#   [PASS] placeholder: 1.00
#   [PASS] style: 1.00
#   [PASS] freshness: 1.00
#   [PASS] length: 0.76
```

### Catch bad output

```python
result = scorer.score("""
I'd be happy to help! According to Smith et al. (2019),
the results for {{QUARTER}} showed [TBD] improvement.
Please verify this with the original source.
""")
print(result)
# ScoreCard: 0.47 [FAIL] (1/5 checks passed)
#   [FAIL] hallucination: 0.77 — Hedging marker, fabricated citation
#   [FAIL] placeholder: 0.60 — Template variable: {{QUARTER}}, TBD marker
#   [FAIL] style: 0.93 — AI tell: 'I'd be happy to'
#   [PASS] freshness: 1.00
#   [FAIL] length: 0.06 — Too short: 32 words
```

### Run an eval suite

```yaml
# eval_suite.yaml
name: "My Quality Suite"
cases:
  - name: "clean_summary"
    prompt: "Summarize today's priorities"
    response: "Three priorities today: ship the API, fix the build, prep for demo."
    expected_keywords: ["priorities"]
    banned_keywords: ["I'd be happy to"]
    min_score: 0.7
```

```bash
llm-eval eval eval_suite.yaml --save baseline.json
# Suite: My Quality Suite — 1/1 passed (100%), avg score: 0.92

# Later, after prompt changes:
llm-eval eval eval_suite.yaml --baseline baseline.json
# ⚠️ REGRESSIONS DETECTED: clean_summary
```

### Log and track costs

```python
from llm_eval_kit import EvalLogger

logger = EvalLogger("my_run.jsonl")

with logger.track("gpt-4o", temperature=0.2) as call:
    call.prompt = "Summarize this document..."
    call.response = my_llm_call(call.prompt)  # your LLM function
    call.input_tokens = 500
    call.output_tokens = 150
    call.cost_usd = 0.003

print(logger.summary())
# {'total_calls': 1, 'total_tokens': 650, 'total_cost_usd': 0.003, ...}
```

```bash
llm-eval costs my_run.jsonl
# Total calls:    1
# Total tokens:   650
# Total cost:     $0.0030
# Avg latency:    342ms
```

---

## Built-in Checks

### Tier 1: Rule-Based (Zero Dependencies)

| Check | What It Detects |
|-------|-----------------|
| `HallucinationCheck` | Hedging phrases, fabricated citations ("Smith et al."), knowledge cutoff references |
| `PlaceholderCheck` | `{{VARIABLES}}`, `[TBD]`, `[TODO]`, `Lorem ipsum`, `<YOUR ...>` |
| `StyleCheck` | AI tells: "I'd be happy to", "Certainly!", "delve", "landscape of", "tapestry" |
| `FreshnessCheck` | Stale year references, outdated "as of" dates |
| `LengthCheck` | Too short (<10 words) or too long (>5000 words) |
| `PIICheck` | Emails, phones, SSNs, credit cards, API keys, AWS keys, GitHub tokens, JWTs |
| `ToxicityCheck` | 3-tier severity: violence (severe), insults (moderate), profanity (mild) |
| `JSONValidityCheck` | Valid JSON? Markdown code blocks? Required keys? Type checking? |
| `CompletenessCheck` | Does output address all questions, numbered items, or required topics from prompt? |
| `ConsistencyCheck` | Self-contradictions: negation pairs, numerical conflicts, explicit contradiction signals |

### Tier 2: LLM-as-Judge (Bring Your Own Key)

| Judge | What It Does |
|-------|--------------|
| `LLMJudge` | G-Eval style — custom criteria → chain-of-thought → 1-5 score. Reference-free or reference-based. |
| `PairwiseJudge` | Compare two outputs — picks winner with confidence (HIGH/MEDIUM/LOW) |
| `RubricJudge` | Score against customizable rubric levels (1-5 with defined descriptions) |

```python
# LLM-as-Judge example
from llm_eval_kit.judges import LLMJudge

judge = LLMJudge(llm_fn=my_llm_function)
result = judge.evaluate(
    output="Revenue grew 15%...",
    criteria="Is this factually accurate and well-structured?",
    prompt="Summarize Q4 results",
)
print(result.score, result.reasoning)
```

### Multi-Model Comparison

```python
from llm_eval_kit import ModelComparator

comparator = ModelComparator()
result = comparator.compare(
    prompt="Summarize Q4 results",
    responses={
        "gpt-4o": "Revenue grew 15%, driven by cloud services...",
        "claude-3": "Q4 showed strong performance across all segments...",
        "llama-3": "The quarterly results indicate positive trends...",
    },
)
print(result)  # Ranked table with per-check scores
print(result.winner)  # "gpt-4o"
```

### HTML Reports

```python
from llm_eval_kit.reporters import HTMLReporter

reporter = HTMLReporter()
html = reporter.scorecard_report(scorecard)  # Radar chart + check table
html = reporter.comparison_report(comparison)  # Bar chart + rankings
reporter.save(html, "report.html")
```

### Add a custom check

```python
from llm_eval_kit.checks.base import Check, CheckResult

class ProfanityCheck(Check):
    name = "profanity"

    def run(self, text: str, **context) -> CheckResult:
        bad_words = ["damn", "hell"]  # your list
        found = [w for w in bad_words if w in text.lower()]
        return CheckResult(
            name=self.name,
            passed=len(found) == 0,
            score=1.0 if not found else 0.0,
            findings=[f"Found: {w}" for w in found],
        )

scorer = Scorer(checks=[ProfanityCheck(), ...])
```

---

## Architecture

```mermaid
flowchart TB
    subgraph INPUT["Input"]
        LLM["LLM Output"]
        SUITE["Eval Suite<br/>YAML/JSON"]
    end

    subgraph TIER1["Tier 1: Rule-Based (Zero Deps)"]
        SC["Scorer"]
        subgraph CHECKS["10 Checks"]
            HC["Hallucination"]
            PC["Placeholder"]
            ST["Style"]
            FR["Freshness"]
            LN["Length"]
            PII["PII"]
            TX["Toxicity"]
            JS["JSON"]
            CM["Completeness"]
            CN["Consistency"]
        end
        SC --> CHECKS
    end

    subgraph TIER2["Tier 2: LLM-as-Judge (Opt-in)"]
        JG["LLMJudge<br/>G-Eval"]
        PW["PairwiseJudge"]
        RB["RubricJudge"]
    end

    subgraph COMPARE["Comparison"]
        MC["ModelComparator"]
    end

    subgraph OUTPUT["Output"]
        CARD["ScoreCard"]
        RPT["HTML / MD<br/>Reports"]
        TBL["Ranked Table"]
    end

    LLM --> SC --> CARD
    LLM --> JG & PW & RB
    LLM --> MC --> TBL
    SUITE --> SC
    CARD --> RPT
    TBL --> RPT
```

See [docs/architecture.md](docs/architecture.md) for detailed design, data flow sequence diagrams, and check lifecycle.
```

---

## CLI Reference

```bash
# Score text directly
llm-eval score "Your LLM output here..."

# Score from file
llm-eval score --file output.txt

# Score from pipe
echo "Your output" | llm-eval score

# Run eval suite
llm-eval eval suite.yaml

# Run with baseline comparison
llm-eval eval suite.yaml --baseline previous_run.json --save current_run.json

# View cost summary
llm-eval costs eval_log.jsonl

# JSON output
llm-eval score --json-output "Your text here"
llm-eval eval suite.yaml --json-output
```

---

## Why Not [existing tool]?

| Tool | Gap |
|------|-----|
| LangSmith | Requires LangChain dependency. Enterprise pricing. |
| promptfoo | Node.js. Config-heavy. Built for prompt engineering, not quality assurance. |
| OpenAI Evals | OpenAI-only. Research-oriented, not production-oriented. |
| ragas | RAG-specific. Heavy deps. Not general-purpose. |
| deepeval | Complex setup. Enterprise-focused. |
| **LLM Eval Kit** | Python-native. 10 checks with zero deps. LLM judge opt-in. Model comparison. HTML reports. 43 tests. CLI. |

---

## Ecosystem

`llm-eval-kit` is part of the [PM Intelligence](https://github.com/kustonaut) toolkit:

| Repo | What It Does |
|------|-------------|
| [issue-sentinel](https://github.com/kustonaut/issue-sentinel) | AI-powered GitHub issue triage |
| [github-issue-analytics](https://github.com/kustonaut/github-issue-analytics) | Visual analytics for GitHub issue data |
| [pm-signals](https://github.com/kustonaut/pm-signals) | Multi-source signal aggregation |
| **llm-eval-kit** | Quality scoring and eval suites for LLM outputs |

---

## Development

```bash
git clone https://github.com/kustonaut/llm-eval-kit.git
cd llm-eval-kit
pip install -e ".[dev]"
pytest --tb=short -q
ruff check src/ tests/
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built by [Akshay Dixit](https://github.com/kustonaut) — because "it looks fine" isn't a quality bar.

</div>
