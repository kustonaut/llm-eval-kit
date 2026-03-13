"""Structured logging for LLM calls — prompt, response, model, latency, tokens, cost."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LLMCall:
    """A single logged LLM interaction."""

    prompt: str
    response: str
    model: str = "unknown"
    temperature: float = 0.0
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EvalLogger:
    """Log LLM calls to JSONL for evaluation and cost tracking.

    Usage:
        logger = EvalLogger("logs/my_run.jsonl")

        with logger.track("gpt-4o", temperature=0.2) as call:
            call.prompt = "Summarize this document..."
            response = my_llm_call(call.prompt)
            call.response = response
            call.input_tokens = 150
            call.output_tokens = 80

        # Or manual logging:
        logger.log(LLMCall(prompt="...", response="...", model="gpt-4o"))
    """

    def __init__(self, log_path: str | Path = "eval_log.jsonl") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._calls: list[LLMCall] = []

    def log(self, call: LLMCall) -> None:
        """Append a call to the log file and in-memory list."""
        self._calls.append(call)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(call.to_dict()) + "\n")

    def track(self, model: str = "unknown", temperature: float = 0.0, **metadata: Any) -> _CallTracker:
        """Context manager that auto-captures latency and logs on exit."""
        return _CallTracker(self, model, temperature, metadata)

    def load(self) -> list[LLMCall]:
        """Load all calls from the log file."""
        calls: list[LLMCall] = []
        if not self.log_path.exists():
            return calls
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    d = json.loads(line)
                    calls.append(LLMCall(**{k: v for k, v in d.items() if k in LLMCall.__dataclass_fields__}))
        return calls

    @property
    def calls(self) -> list[LLMCall]:
        return list(self._calls)

    def summary(self) -> dict[str, Any]:
        """Aggregate stats across all logged calls."""
        calls = self._calls or self.load()
        if not calls:
            return {"total_calls": 0}
        total_cost = sum(c.cost_usd for c in calls)
        total_tokens = sum(c.total_tokens for c in calls)
        avg_latency = sum(c.latency_ms for c in calls) / len(calls)
        models = set(c.model for c in calls)
        return {
            "total_calls": len(calls),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 1),
            "models_used": sorted(models),
        }


class _CallTracker:
    """Context manager for auto-timing LLM calls."""

    def __init__(self, logger: EvalLogger, model: str, temperature: float, metadata: dict[str, Any]) -> None:
        self._logger = logger
        self._call = LLMCall(prompt="", response="", model=model, temperature=temperature, metadata=metadata)
        self._start: float = 0.0

    def __enter__(self) -> LLMCall:
        self._start = time.perf_counter()
        return self._call

    def __exit__(self, *exc: Any) -> None:
        self._call.latency_ms = round((time.perf_counter() - self._start) * 1000, 1)
        self._logger.log(self._call)
