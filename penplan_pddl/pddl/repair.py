"""Constrained repair logic for PenPlan-PDDL plans.

This module implements the repair mechanism from Equation 13:
Δπ* = argmin d(π, π ⊕ Δπ)
s.t. I --[D]--> G via (π ⊕ Δπ), J(π ⊕ Δπ) ≤ κ

The repair loop searches for minimal edits that restore feasibility
while keeping cost under threshold κ.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional
import copy

from ..plan import Plan, PlanStep, ValidationIssue
from .domain import ActionDefinition, Domain
from .problem import PlanningProblem


@dataclass
class RepairLibraryEntry:
    fact: str
    builder: Callable[[], PlanStep]
    cost: float
    risk: float


@dataclass
class RepairResult:
    """Result of a repair attempt."""
    success: bool
    repaired_plan: Optional[Plan]
    edits_applied: int
    additional_cost: float
    message: str


def _action_from_step(step: PlanStep) -> ActionDefinition:
    return ActionDefinition(
        name=step.action_id,
        preconditions=set(step.preconditions),
        add_effects={effect for effect in step.effects if not effect.startswith("not ")},
        del_effects={effect[4:] for effect in step.effects if effect.startswith("not ")},
        cost=step.cost,
        risk=step.risk,
    )


def _edit_distance(original: Plan, modified: Plan) -> int:
    """Calculate minimal edit distance d(π, π ⊕ Δπ).

    Simplified implementation counting insertions and deletions.
    """
    return abs(len(original) - len(modified))


class PlanRepairer:
    """Injects lightweight corrective steps when validation fails.

    Implements Equation 13 from paper:
    - Minimizes edit distance d(π, π ⊕ Δπ)
    - Ensures reachability: I --[D]--> G
    - Respects cost constraint: J(π ⊕ Δπ) ≤ κ
    """

    def __init__(self, cost_threshold: float = 50.0) -> None:
        """Initialize repairer.

        Args:
            cost_threshold: Maximum allowed cost κ for repaired plan
        """
        self.cost_threshold = cost_threshold
        self._library: Dict[str, RepairLibraryEntry] = {
            "mission_received": RepairLibraryEntry(
                fact="mission_received",
                builder=lambda: PlanStep(
                    action_id="ingest_mission",
                    description="Register mission tasking and baseline objectives.",
                    role="Manager",
                    layer="strategic",
                    preconditions=set(),
                    effects={"mission_received"},
                    risk=0.0,
                    cost=0.4,
                ),
                cost=0.4,
                risk=0.0,
            ),
            "campaign_sequence_prepared": RepairLibraryEntry(
                fact="campaign_sequence_prepared",
                builder=lambda: PlanStep(
                    action_id="synchronize_campaign",
                    description="Synchronize campaign ordering across agents.",
                    role="Commander",
                    layer="strategic",
                    preconditions={"goals_established"},
                    effects={"campaign_sequence_prepared"},
                    risk=0.01,
                    cost=0.6,
                ),
                cost=0.6,
                risk=0.01,
            ),
            "opsec_measures_established": RepairLibraryEntry(
                fact="opsec_measures_established",
                builder=lambda: PlanStep(
                    action_id="deploy_opsec_controls",
                    description="Deploy compensating controls to restore OPSEC discipline.",
                    role="Opsec",
                    layer="tactical",
                    preconditions=set(),
                    effects={"opsec_measures_established"},
                    risk=0.03,
                    cost=0.7,
                ),
                cost=0.7,
                risk=0.03,
            ),
            "initial_access_vector_prepared": RepairLibraryEntry(
                fact="initial_access_vector_prepared",
                builder=lambda: PlanStep(
                    action_id="refresh_access_vector",
                    description="Refresh initial access preparation with updated recon data.",
                    role="SocialEngineer",
                    layer="tactical",
                    preconditions={"reconnaissance_intelligence_collected"},
                    effects={"initial_access_vector_prepared"},
                    risk=0.05,
                    cost=0.8,
                ),
                cost=0.8,
                risk=0.05,
            ),
            "access_obtained": RepairLibraryEntry(
                fact="access_obtained",
                builder=lambda: PlanStep(
                    action_id="re_execute_exploit",
                    description="Re-run exploit chain with mitigated risk profile.",
                    role="Exploiter",
                    layer="technical",
                    preconditions={"initial_access_vector_prepared"},
                    effects={"access_obtained"},
                    risk=0.06,
                    cost=1.0,
                ),
                cost=1.0,
                risk=0.06,
            ),
        }

    def attempt_repair(
        self,
        plan: Plan,
        domain: Domain,
        problem: PlanningProblem,
        issue: ValidationIssue,
        current_cost: float = 0.0,
    ) -> RepairResult:
        """Attempt to repair a plan by injecting corrective actions.

        Implements Equation 13:
        Δπ* = argmin d(π, π ⊕ Δπ)
        s.t. I --[D]--> G via (π ⊕ Δπ), J(π ⊕ Δπ) ≤ κ

        Args:
            plan: Original plan with validation issues
            domain: PDDL domain definition
            problem: PDDL problem instance
            issue: Validation issue to repair
            current_cost: Current plan cost J(π)

        Returns:
            RepairResult with success status and repaired plan if successful
        """
        # Try to find minimal repair for missing preconditions
        best_repair = None
        min_cost = float('inf')

        for missing in issue.missing_preconditions:
            entry = self._library.get(missing)
            if entry is None:
                continue

            # Calculate cost of this repair
            repair_cost = current_cost + entry.cost

            # Check cost constraint: J(π ⊕ Δπ) ≤ κ
            if repair_cost > self.cost_threshold:
                continue

            # This repair satisfies constraints and has lower cost
            if repair_cost < min_cost:
                best_repair = entry
                min_cost = repair_cost

        # Apply best repair if found
        if best_repair is not None:
            # Create copy of plan for repair
            repaired_plan = copy.deepcopy(plan)
            step = best_repair.builder()

            # Insert repair action minimizing edit distance
            repaired_plan.insert(issue.index, step)

            # Add action to domain
            domain.add_action(_action_from_step(step))

            return RepairResult(
                success=True,
                repaired_plan=repaired_plan,
                edits_applied=1,
                additional_cost=best_repair.cost,
                message=f"Injected {step.action_id} to establish {best_repair.fact}"
            )
        else:
            return RepairResult(
                success=False,
                repaired_plan=None,
                edits_applied=0,
                additional_cost=0.0,
                message=f"No feasible repair found within cost threshold κ={self.cost_threshold}"
            )

    def repair_loop(
        self,
        plan: Plan,
        domain: Domain,
        problem: PlanningProblem,
        max_iterations: int = 3
    ) -> RepairResult:
        """Execute complete repair loop with multiple iterations.

        Args:
            plan: Plan to repair
            domain: PDDL domain
            problem: PDDL problem
            max_iterations: Maximum repair iterations

        Returns:
            Final repair result after all iterations
        """
        from .solver import PlanValidator  # avoid circular import

        current_plan = copy.deepcopy(plan)
        total_edits = 0
        total_cost_added = 0.0

        validator = PlanValidator(domain, problem)

        for iteration in range(max_iterations):
            # Validate current plan
            validation = validator.validate(current_plan)

            if validation.success:
                return RepairResult(
                    success=True,
                    repaired_plan=current_plan,
                    edits_applied=total_edits,
                    additional_cost=total_cost_added,
                    message=f"Plan repaired successfully after {iteration} iterations"
                )

            if not validation.issues:
                break

            # Attempt repair for first issue
            first_issue = validation.issues[0]
            repair_result = self.attempt_repair(
                current_plan,
                domain,
                problem,
                first_issue,
                validation.plan_cost
            )

            if not repair_result.success:
                return repair_result

            # Update plan with repair
            current_plan = repair_result.repaired_plan
            total_edits += repair_result.edits_applied
            total_cost_added += repair_result.additional_cost

        # Max iterations reached without full repair
        return RepairResult(
            success=False,
            repaired_plan=current_plan,
            edits_applied=total_edits,
            additional_cost=total_cost_added,
            message=f"Repair incomplete after {max_iterations} iterations"
        )


__all__ = ["PlanRepairer", "RepairLibraryEntry", "RepairResult"]
