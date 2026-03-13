# Architecture

## Design Principles

1. **Zero LLM dependencies for scoring** — You don't need an API key to evaluate text. All built-in checks are regex/rule-based.
2. **Pluggable checks** — Subclass `Check`, implement `run()`, done. No framework lock-in.
3. **YAML-first test suites** — Define golden test cases in YAML, not code. PMs can write eval suites without Python knowledge.
4. **Regression-aware** — Every eval run can be compared against a baseline. Quality drops are caught before production.
5. **Model-agnostic** — Works with pre-computed responses, any LLM API, or local models. The scorer doesn't care where the text came from.

## Component Overview

```mermaid
flowchart TB
    subgraph INPUT["Input"]
        LLM["LLM Output\n(text string)"]
        SUITE["Eval Suite\n(YAML/JSON)"]
        LOG["Call Log\n(JSONL)"]
    end

    subgraph SCORING["Scoring Engine"]
        SC["Scorer"]
        subgraph CHECKS["Pluggable Checks"]
            HC["Hallucination"]
            PC["Placeholder"]
            ST["Style"]
            FR["Freshness"]
            LN["Length"]
            CU["+ Custom"]
        end
        SC --> HC & PC & ST & FR & LN & CU
    end

    subgraph EVAL["Eval Runner"]
        ER["EvalRunner"]
        KW["Keyword\nChecks"]
        REG["Regression\nDetection"]
        ER --> KW & REG
    end

    subgraph OUTPUT["Output"]
        CARD["ScoreCard"]
        SR["SuiteResult"]
        BASE["Baseline\n(JSON)"]
    end

    LLM --> SC --> CARD
    SUITE --> ER
    ER --> SC
    ER --> SR
    SR --> BASE
    BASE -.->|compare| REG

    subgraph LOGGER["Logger"]
        EL["EvalLogger"]
        JSONL["JSONL File"]
        SUM["Summary\n(tokens, cost, latency)"]
        EL --> JSONL --> SUM
    end

    LLM -.->|track| EL
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User/CI
    participant S as Scorer
    participant C as Checks[]
    participant R as EvalRunner
    participant B as Baseline

    Note over U,B: Single Output Scoring
    U->>S: score(text)
    S->>C: run(text) for each check
    C-->>S: CheckResult[]
    S-->>U: ScoreCard (score, pass/fail, findings)

    Note over U,B: Suite Evaluation
    U->>R: run(test_cases, responses)
    loop For each test case
        R->>S: score(response)
        S-->>R: ScoreCard
        R->>R: Check keywords + banned words
    end
    R-->>U: SuiteResult

    Note over U,B: Regression Detection
    U->>R: result.regressions(baseline)
    R->>B: Load previous SuiteResult
    R->>R: Compare pass/fail per test
    R-->>U: List of regressed test names
```

## Check Lifecycle

```mermaid
flowchart LR
    subgraph CHECK["Check.run(text)"]
        direction TB
        A["Match patterns\nagainst text"] --> B["Collect findings"]
        B --> C["Calculate score\n0.0 to 1.0"]
        C --> D["Return CheckResult\npassed + score + findings"]
    end

    TEXT["LLM Output"] --> CHECK
    CHECK --> RESULT["CheckResult"]
```

## Check Interface

Every check implements:

```python
class Check(ABC):
    name: str

    def run(self, text: str, **context) -> CheckResult:
        # context may include: prompt, model, temperature, metadata
        ...
```

Returns:
- `CheckResult.passed: bool` — binary pass/fail
- `CheckResult.score: float` — 0.0 (worst) to 1.0 (best)
- `CheckResult.findings: list[str]` — human-readable issues found

## Scoring

The `Scorer` averages all check scores for an `overall_score`. A configurable `threshold` (default 0.7) determines the overall pass/fail.

## Eval Runner

The `EvalRunner` adds:
- **Expected keywords** — test case must contain these words
- **Banned keywords** — test case must NOT contain these words
- **Regression detection** — compare `SuiteResult` against a previous `SuiteResult`

## Storage

- **Eval logs**: JSONL (one line per LLM call) — append-only, grep-friendly
- **Suite results**: JSON — for baseline comparison
- **Test suites**: YAML/JSON — human-editable
