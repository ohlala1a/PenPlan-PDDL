"""Command line entry point for running the PenPlan-PDDL pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .config import PenPlanConfig
from .pipeline import PenPlanPipeline


def _load_scenario(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _format_step(index: int, step) -> str:
    preconditions = ", ".join(sorted(step.preconditions)) or "none"
    effects = ", ".join(sorted(step.effects)) or "none"
    return (
        f"[{index:02d}] {step.action_id} ({step.role}/{step.layer})\n"
        f"     {step.description}\n"
        f"     preconditions: {preconditions}\n"
        f"     effects: {effects}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PenPlan-PDDL planning pipeline")
    parser.add_argument(
        "scenario",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "scenarios" / "example_scenario.json"),
        help="Path to a scenario JSON file",
    )
    args = parser.parse_args(argv)

    scenario = _load_scenario(Path(args.scenario))
    pipeline = PenPlanPipeline(PenPlanConfig())
    result = pipeline.plan(scenario)

    print("=== Retrieved Context Nodes ===")
    for node_id in result.retrieved_context:
        print(f" - {node_id}")

    print("\n=== Plan Steps ===")
    for idx, step in enumerate(result.plan.steps):
        print(_format_step(idx, step))

    print("=== Validation ===")
    if result.report.success:
        print("Plan satisfies goals and risk budget.")
    else:
        print("Plan failed validation.")
        for issue in result.report.issues:
            missing = ", ".join(sorted(issue.missing_preconditions)) or "none"
            print(
                f" - Step {issue.index} missing: {missing}; exceeded risk: {issue.exceeded_risk}"
            )

    print("\nGoals:", ", ".join(sorted(result.problem.goals)))
    print("Final state contains", len(result.report.final_state), "facts.")
    return 0 if result.report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
