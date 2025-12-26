"""Plan validation and PDDL solving utilities with Fast-Downward integration.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Optional, Dict, Any
import subprocess
import tempfile
from pathlib import Path
import time

from ..plan import Plan, PlanState, PlanStep, ValidationIssue
from .domain import ActionDefinition, Domain
from .problem import PlanningProblem


@dataclass
class ValidationReport:
    success: bool
    final_state: Set[str]
    issues: List[ValidationIssue]
    plan_cost: float = 0.0
    total_risk: float = 0.0
    plan_length: int = 0


@dataclass
class SolverResult:
    """Result from Fast-Downward solver."""
    success: bool
    plan: Optional[Plan]
    solve_time: float
    plan_cost: float
    stderr: str = ""


class PlanValidator:
    """Simulates execution of a plan against a domain/problem pair.

    Implements cost function from paper (Equations 11-12):
    J(π) = λ1*L(π) + λ2*R(π) + λ3*C_res(π)
    where λ1=0.2, λ2=0.4, λ3=0.4
    """

    # Cost function weights from paper
    LAMBDA_LENGTH = 0.2  # λ1: plan length weight
    LAMBDA_RISK = 0.4    # λ2: detection risk weight
    LAMBDA_RESOURCE = 0.4  # λ3: resource consumption weight

    def __init__(self, domain: Domain, problem: PlanningProblem) -> None:
        if domain.name != problem.domain_name:
            raise ValueError("Domain and problem names must match")
        self.domain = domain
        self.problem = problem

    def validate(self, plan: Plan) -> ValidationReport:
        """Validate plan with cost and risk tracking."""
        state = PlanState(set(self.problem.initial_state))
        accumulated_risk = 0.0
        accumulated_cost = 0.0
        issues: List[ValidationIssue] = []

        for index, step in enumerate(plan):
            action = self._as_action(step)
            missing = {fact for fact in action.preconditions if fact not in state.facts}
            accumulated_risk += action.risk
            accumulated_cost += action.cost
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

        # Calculate composite cost using paper's formula
        plan_length = len(plan)
        composite_cost = (
            self.LAMBDA_LENGTH * plan_length +
            self.LAMBDA_RISK * accumulated_risk +
            self.LAMBDA_RESOURCE * accumulated_cost
        )

        return ValidationReport(
            success=success,
            final_state=set(state.facts),
            issues=issues,
            plan_cost=composite_cost,
            total_risk=accumulated_risk,
            plan_length=plan_length
        )

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


class FastDownwardSolver:
    """Integration with Fast-Downward PDDL planner.

    Configuration from paper and rebuttal:
    - Timeout: 10 seconds
    - Search algorithm: A* (astar)
    - Heuristic: Blind heuristic
    """

    TIMEOUT_SECONDS = 10  # 10s timeout as stated in rebuttal

    def __init__(self, fast_downward_path: str = "fast-downward"):
        """Initialize solver.

        Args:
            fast_downward_path: Path to fast-downward executable
        """
        self.fd_path = fast_downward_path

    def solve(
        self,
        domain: Domain,
        problem: PlanningProblem,
        use_blind: bool = True
    ) -> SolverResult:
        """Solve PDDL problem using Fast-Downward.

        Args:
            domain: PDDL domain definition
            problem: PDDL problem instance
            use_blind: If True, use blind heuristic (default from paper)

        Returns:
            SolverResult with plan if solvable
        """
        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write domain and problem to temp files
            domain_file = tmppath / "domain.pddl"
            problem_file = tmppath / "problem.pddl"

            domain_file.write_text(self._domain_to_pddl(domain), encoding="utf-8")
            problem_file.write_text(self._problem_to_pddl(problem), encoding="utf-8")

            # Configure A* search with blind heuristic as per paper
            if use_blind:
                search_config = "astar(blind())"
            else:
                search_config = "astar(lmcut())"

            # Run Fast-Downward
            cmd = [
                self.fd_path,
                str(domain_file),
                str(problem_file),
                "--search",
                search_config
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.TIMEOUT_SECONDS,
                    cwd=str(tmppath)
                )

                solve_time = time.time() - start_time

                # Check for solution
                sas_plan = tmppath / "sas_plan"
                if sas_plan.exists():
                    plan_text = sas_plan.read_text(encoding="utf-8")
                    plan = self._parse_plan(plan_text, domain)

                    # Calculate plan cost
                    validator = PlanValidator(domain, problem)
                    validation = validator.validate(plan)

                    return SolverResult(
                        success=True,
                        plan=plan,
                        solve_time=solve_time,
                        plan_cost=validation.plan_cost,
                        stderr=result.stderr
                    )
                else:
                    return SolverResult(
                        success=False,
                        plan=None,
                        solve_time=solve_time,
                        plan_cost=0.0,
                        stderr=result.stderr
                    )

            except subprocess.TimeoutExpired:
                return SolverResult(
                    success=False,
                    plan=None,
                    solve_time=self.TIMEOUT_SECONDS,
                    plan_cost=0.0,
                    stderr="Timeout after 10 seconds"
                )
            except Exception as e:
                return SolverResult(
                    success=False,
                    plan=None,
                    solve_time=time.time() - start_time,
                    plan_cost=0.0,
                    stderr=str(e)
                )

    def _domain_to_pddl(self, domain: Domain) -> str:
        """Convert domain to PDDL text."""
        # Simplified - assumes domain already has PDDL representation
        # In full implementation, would generate from Domain object
        return f"(define (domain {domain.name})\n  ;; domain stub\n)"

    def _problem_to_pddl(self, problem: PlanningProblem) -> str:
        """Convert problem to PDDL text."""
        # Simplified - assumes problem already has PDDL representation
        return f"(define (problem {problem.problem_name})\n  ;; problem stub\n)"

    def _parse_plan(self, plan_text: str, domain: Domain) -> Plan:
        """Parse Fast-Downward solution into Plan object."""
        steps = []
        for line in plan_text.strip().split('\n'):
            if line.startswith(';') or not line.strip():
                continue
            # Parse action from plan
            # Format: (action-name param1 param2 ...)
            action_name = line.strip().strip('()').split()[0]

            # Create plan step (simplified)
            step = PlanStep(
                action_id=action_name,
                description=f"Execute {action_name}",
                role="",
                layer="",
                preconditions=set(),
                effects=set(),
                cost=1.0,
                risk=0.0
            )
            steps.append(step)

        return Plan(steps)


__all__ = ["PlanValidator", "ValidationReport", "FastDownwardSolver", "SolverResult"]
