from __future__ import annotations

import json
from pathlib import Path

from penplan_pddl import PenPlanConfig, PenPlanPipeline


def load_scenario() -> dict:
    scenario_path = Path(__file__).resolve().parent.parent / "scenarios" / "example_scenario.json"
    return json.loads(scenario_path.read_text(encoding="utf-8"))


def test_pipeline_produces_valid_plan():
    pipeline = PenPlanPipeline(PenPlanConfig())
    result = pipeline.plan(load_scenario())

    assert result.report.success, "Plan should satisfy verification criteria"
    assert len(result.plan.steps) > 0
    assert len(result.plan.steps) <= pipeline.config.verification.max_plan_length
    for goal in result.problem.goals:
        assert goal in result.report.final_state
