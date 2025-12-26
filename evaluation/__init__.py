"""Evaluation package for PenPlan-PDDL.

Provides baseline implementations and evaluation protocols
for reproducing paper results.
"""

from .baselines import (
    BaselineMethod,
    BaselineResult,
    AutoGPTBaseline,
    PentestGPTBaseline,
    CyAgentBaseline,
    TAgentBaseline,
    RuleBasedBaseline,
    get_baseline,
)

from .evaluator import (
    AuroraEvaluator,
    CVEBenchEvaluator,
    EvaluationMetrics,
    run_full_evaluation,
)

__all__ = [
    # Baselines
    "BaselineMethod",
    "BaselineResult",
    "AutoGPTBaseline",
    "PentestGPTBaseline",
    "CyAgentBaseline",
    "TAgentBaseline",
    "RuleBasedBaseline",
    "get_baseline",
    # Evaluators
    "AuroraEvaluator",
    "CVEBenchEvaluator",
    "EvaluationMetrics",
    "run_full_evaluation",
]
