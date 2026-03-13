# LinkedIn Post — LLM Eval Kit v0.2.0

## Main Post

Shipped v0.2 of LLM Eval Kit.
10 quality checks. 3 LLM judges. Multi-model comparison.
Zero API keys needed.

The problem hasn’t changed:
You changed a prompt. Did the output get better?
"It looks fine" isn't a quality bar. Numbers are.

What’s new in v0.2:

→ 10 rule-based checks (zero deps, zero API keys):
  Hallucination · Placeholder · Style · Freshness · Length
  PII detection · Toxicity · JSON validity · Completeness · Consistency

→ 3 LLM-as-Judge evaluators (bring your own key):
  G-Eval style judge · Pairwise comparison · Rubric-based grading

→ Multi-model comparison:
  Run same prompt through N models. Ranked table. Per-check breakdown.

→ HTML + Markdown reports:
  Dark-themed reports with Chart.js radar/bar charts.
  Paste into a PR or share with your team.

43 tests. MIT licensed. Python 3.10+.

🔗 github.com/kustonaut/llm-eval-kit
🎮 Try the demo: kustonaut.github.io/llm-eval-kit
📦 pip install llm-eval-kit

#AI #LLM #Evals #QualityEngineering #OpenSource #Python

---

## Carousel Slides (for LinkedIn carousel PDF)

### Slide 1: Cover
LLM EVAL KIT
10 checks. 3 judges. Zero API keys.
Stop shipping vibes.

### Slide 2: The Problem
You changed a prompt.
Did the output get better or worse?

Most teams: read it → "looks fine" → ship it
Reality: no regression detection, no quality tracking, no numbers

### Slide 3: Tier 1 — Rule-Based (Zero Deps)
10 checks that run offline, instantly, with no API key:

✔ Hallucination — hedging, fake citations
✔ Placeholder — {{VAR}}, [TBD], Lorem ipsum
✔ Style — AI tells ("delve", "tapestry")
✔ Freshness — stale dates
✔ Length — too short / too long
✔ PII — emails, SSNs, API keys
✔ Toxicity — 3-tier severity
✔ JSON — valid? schema match?
✔ Completeness — all prompt parts addressed?
✔ Consistency — self-contradictions

### Slide 4: Tier 2 — LLM-as-Judge (Opt-in)
Bring your own key. Any provider.

🧑‍⚖️ G-Eval Judge — custom criteria → CoT → score
⚔️ Pairwise Judge — compare A vs B, pick winner
📊 Rubric Judge — score against defined levels

Works with: OpenAI, Anthropic, Ollama, any callable

### Slide 5: Multi-Model Comparison
Same prompt. N models. Ranked results.

```
comparator = ModelComparator()
result = comparator.compare(
    prompt="Summarize Q4...",
    responses={"gpt-4o": "...", "claude": "...", "llama": "..."},
)
print(result.winner)  # "gpt-4o"
```

### Slide 6: Reports
HTML reports with Chart.js charts (dark theme)
Markdown reports for GitHub PRs
Radar charts per scorecard
Bar charts for model comparison

### Slide 7: The Unique Value
Why this exists alongside promptfoo, ragas, deepeval:

✔ Zero-to-eval in 5 minutes
✔ Rule-based scoring needs zero API keys
✔ LLM judge is opt-in, not required
✔ Python-native (not Node.js)
✔ 43 tests passing
✔ Interactive demo (runs in browser)

### Slide 8: CTA
🔗 github.com/kustonaut/llm-eval-kit
🎮 kustonaut.github.io/llm-eval-kit
📦 pip install llm-eval-kit

4th tool in the PM Intelligence toolkit:
1. issue-sentinel — AI-powered issue triage
2. github-issue-analytics — visual analytics
3. pm-signals — signal aggregation
4. llm-eval-kit — LLM quality scoring ← NEW
