Changed a prompt last week.
Didn't realize the output quality dropped until a customer noticed.

That's when I built LLM Eval Kit.

---

The problem:
Most teams evaluate LLM output by reading it.
That doesn't scale. It doesn't catch regressions.
And "it looks fine" isn't a quality bar.

The solution:
5 built-in quality checks. Zero API keys required.

→ Hallucination detection (hedging phrases, fabricated citations)
→ Placeholder detection ({{UNFILLED_VARIABLES}}, [TBD], Lorem ipsum)
→ AI tell detection ("I'd be happy to help!", "delve", "tapestry")
→ Freshness check (stale year references)
→ Length validation (too short / too long)

Plus:
→ Golden test suites in YAML — define once, run forever
→ Regression detection — compare runs against baselines
→ Cost + latency tracking per LLM call
→ Pluggable — add your own checks in 10 lines

---

How it works:

```
from llm_eval_kit import Scorer
scorer = Scorer()
result = scorer.score("Your LLM output...")
# ScoreCard: 0.95 [PASS] (5/5 checks passed)
```

One number. Pass or fail. Every time.

---

Open source. MIT licensed. Python 3.10+.

🔗 github.com/kustonaut/llm-eval-kit
🎮 Try the demo: kustonaut.github.io/llm-eval-kit
📦 pip install llm-eval-kit

#AI #LLM #ProductManagement #QualityEngineering #OpenSource #Python

---

4th tool in the PM Intelligence toolkit:
1. issue-sentinel — AI-powered GitHub issue triage
2. github-issue-analytics — visual analytics for issue data
3. pm-signals — multi-source signal aggregation
4. llm-eval-kit — quality scoring for LLM outputs ← NEW

More at github.com/kustonaut
