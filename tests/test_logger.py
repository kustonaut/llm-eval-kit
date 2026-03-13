"""Tests for the logger."""

import json
import tempfile
from pathlib import Path

from llm_eval_kit.logger import EvalLogger, LLMCall


def test_log_and_load():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        log_path = f.name

    logger = EvalLogger(log_path)
    logger.log(LLMCall(
        prompt="Hello",
        response="Hi there",
        model="gpt-4o",
        temperature=0.2,
        input_tokens=5,
        output_tokens=3,
        cost_usd=0.0001,
    ))

    loaded = logger.load()
    assert len(loaded) == 1
    assert loaded[0].prompt == "Hello"
    assert loaded[0].model == "gpt-4o"
    assert loaded[0].total_tokens == 8

    Path(log_path).unlink()


def test_track_context_manager():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        log_path = f.name

    logger = EvalLogger(log_path)

    with logger.track("claude-3", temperature=0.5) as call:
        call.prompt = "Test prompt"
        call.response = "Test response"
        call.input_tokens = 10
        call.output_tokens = 20

    assert len(logger.calls) == 1
    assert logger.calls[0].latency_ms >= 0  # may be 0.0 on very fast CPUs
    assert logger.calls[0].model == "claude-3"

    Path(log_path).unlink()


def test_summary():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        log_path = f.name

    logger = EvalLogger(log_path)
    for i in range(5):
        logger.log(LLMCall(
            prompt=f"prompt {i}",
            response=f"response {i}",
            model="gpt-4o" if i < 3 else "claude-3",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            latency_ms=200 + i * 10,
        ))

    summary = logger.summary()
    assert summary["total_calls"] == 5
    assert summary["total_tokens"] == 750
    assert summary["total_cost_usd"] == 0.005
    assert "gpt-4o" in summary["models_used"]
    assert "claude-3" in summary["models_used"]

    Path(log_path).unlink()
