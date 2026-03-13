"""CLI for llm-eval-kit — score, eval, report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from llm_eval_kit.scorer import Scorer
from llm_eval_kit.eval_runner import EvalRunner
from llm_eval_kit.logger import EvalLogger


@click.group()
@click.version_option()
def main() -> None:
    """LLM Eval Kit — Quality scoring and eval suites for LLM outputs."""


@main.command()
@click.argument("text", required=False)
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="Score text from a file.")
@click.option("--threshold", default=0.7, type=float, help="Pass/fail threshold (0.0-1.0).")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
def score(text: str | None, file_path: str | None, threshold: float, as_json: bool) -> None:
    """Score LLM output quality.

    Pass text directly or use --file to score file contents.
    """
    if file_path:
        content = Path(file_path).read_text(encoding="utf-8")
    elif text:
        content = text
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        click.echo("Provide text as argument, --file, or pipe via stdin.", err=True)
        raise SystemExit(1)

    scorer = Scorer(threshold=threshold)
    result = scorer.score(content)

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(result)


@main.command(name="eval")
@click.argument("suite_path", type=click.Path(exists=True))
@click.option("--baseline", type=click.Path(exists=True), help="Baseline result JSON for regression detection.")
@click.option("--save", "save_path", type=click.Path(), help="Save result to JSON.")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
def eval_suite(suite_path: str, baseline: str | None, save_path: str | None, as_json: bool) -> None:
    """Run an eval suite (YAML/JSON) against pre-computed responses.

    Suite file format:
        name: "My Suite"
        cases:
          - name: "test_1"
            prompt: "..."
            response: "..."  # pre-computed
            expected_keywords: ["word1", "word2"]
    """
    runner = EvalRunner()
    suite_name, cases = runner.load_suite(suite_path)

    # Load responses from suite file (for offline eval)
    import yaml
    with open(suite_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) if suite_path.endswith((".yaml", ".yml")) else json.load(f)

    responses = {}
    for c in data.get("cases", []):
        if "response" in c:
            responses[c["name"]] = c["response"]

    result = runner.run(cases, suite_name=suite_name, responses=responses)

    # Regression check
    if baseline:
        base = runner.load_baseline(baseline)
        regressions = result.regressions(base)
        if regressions:
            click.echo(f"\n⚠️  REGRESSIONS DETECTED: {', '.join(regressions)}", err=True)

    if save_path:
        runner.save_result(result, save_path)
        click.echo(f"Result saved to {save_path}")

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(result)


@main.command()
@click.argument("log_path", type=click.Path(exists=True))
def costs(log_path: str) -> None:
    """Show cost and latency summary from an eval log."""
    logger = EvalLogger(log_path)
    summary = logger.summary()

    if summary["total_calls"] == 0:
        click.echo("No calls logged.")
        return

    click.echo(f"Total calls:    {summary['total_calls']}")
    click.echo(f"Total tokens:   {summary['total_tokens']:,}")
    click.echo(f"Total cost:     ${summary['total_cost_usd']:.4f}")
    click.echo(f"Avg latency:    {summary['avg_latency_ms']:.0f}ms")
    click.echo(f"Models used:    {', '.join(summary['models_used'])}")


if __name__ == "__main__":
    main()
