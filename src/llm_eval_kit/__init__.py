"""LLM Eval Kit — Quality scoring, eval suites, and regression detection for LLM outputs."""

__version__ = "0.1.0"

from llm_eval_kit.logger import EvalLogger
from llm_eval_kit.scorer import Scorer
from llm_eval_kit.eval_runner import EvalRunner

__all__ = ["EvalLogger", "Scorer", "EvalRunner", "__version__"]
