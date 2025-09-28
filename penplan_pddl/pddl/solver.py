"""Plan validation utilities using minimal STRIPS-style reasoning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from ..plan import Plan, PlanState, PlanStep, ValidationIssue
from .domain import ActionDefinition, Domain
from .problem import PlanningProblem


@dataclass
class ValidationReport:
    success: bool
    final_state: Set[str]
    issues: List[ValidationIssue]


class PlanValidator:
    """Simulates execution of a plan against a domain/problem pair."""

    def __init__(self, domain: Domain, problem: PlanningProblem) -> None:
        if domain.name != problem.domain_name:
            raise ValueError("Domain and problem names must match")
        self.domain = domain
        self.problem = problem

    def validate(self, plan: Plan) -> ValidationReport:
        state = PlanState(set(self.problem.initial_state))
        accumulated_risk = 0.0
        issues: List[ValidationIssue] = []

        for index, step in enumerate(plan):
            action = self._as_action(step)
            missing = {fact for fact in action.preconditions if fact not in state.facts}
            accumulated_risk += action.risk
            exceeded_risk = accumulated_risk > self.problem.risk_budget
            if missing or exceeded_risk:
                issues.append(
                    ValidationIssue(
                        index=index,
                        step=step,
                        missing_preconditions=missing,
                        exceeded_risk=exceeded_risk,
                    )
                )
                if missing:
                    continue
            state.apply(action.add_effects)
            for fact in action.del_effects:
                state.facts.discard(fact)

        goal_satisfied = self.problem.goals.issubset(state.facts)
        success = not issues and goal_satisfied
        return ValidationReport(success=success, final_state=set(state.facts), issues=issues)

    def _as_action(self, step: PlanStep) -> ActionDefinition:
        try:
            return self.domain.find_action(step.action_id)
        except KeyError as exc:  # fall back to step definition directly
            return ActionDefinition(
                name=step.action_id,
                preconditions=set(step.preconditions),
                add_effects=set(effect for effect in step.effects if not effect.startswith("not ")),
                del_effects={effect[4:] for effect in step.effects if effect.startswith("not ")},
                cost=step.cost,
                risk=step.risk,
            )


__all__ = ["PlanValidator", "ValidationReport"]
