"""Main orchestration pipeline for the public PenPlan-PDDL release."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from .agents import AgentContext, ROLE_IMPLEMENTATIONS
from .config import PenPlanConfig, RoleConfig
from .knowledge_graph import KnowledgeGraph
from .plan import Plan, PlanState, PlanStep
from .pddl import ActionDefinition, Domain, PlanRepairer, PlanValidator, PlanningProblem, ValidationReport
from .utils import HashingVectorizer


@dataclass
class PipelineResult:
    plan: Plan
    domain: Domain
    problem: PlanningProblem
    report: ValidationReport
    retrieved_context: Sequence[str]


class PenPlanPipeline:
    """Co-ordinates knowledge retrieval, multi-agent planning, and PDDL verification."""

    def __init__(self, config: PenPlanConfig | None = None, graph_path: Path | None = None):
        self.config = config or PenPlanConfig()
        self.vectorizer = HashingVectorizer()
        data_dir = Path(__file__).resolve().parent / "data"
        graph_path = graph_path or (data_dir / "knowledge_graph.json")
        if not graph_path.exists():
            raise FileNotFoundError(f"Knowledge graph file not found at {graph_path}")
        self.graph = KnowledgeGraph.from_json(graph_path, vectorizer=self.vectorizer)
        self.agents = self._instantiate_agents(self.config.roles)
        self.repairer = PlanRepairer()

    def _instantiate_agents(self, role_configs: Iterable[RoleConfig]):
        agents = []
        for role in role_configs:
            implementation = ROLE_IMPLEMENTATIONS.get(role.name)
            if implementation is None:
                continue
            agents.append(implementation(role.name, role.layer, role.weight, role.objectives))
        return agents

    def plan(self, scenario: Dict[str, Any]) -> PipelineResult:
        retrieved = self.graph.retrieve(
            query=self._scenario_to_query(scenario),
            top_k=self.config.retrieval.top_k,
            semantic_weight=self.config.retrieval.semantic_weight,
            structural_weight=self.config.retrieval.structural_weight,
            similarity_threshold=self.config.retrieval.similarity_threshold,
            vectorizer=self.vectorizer,
        )
        retrieved_nodes = [node for node, _score in retrieved]
        plan = Plan()
        domain = Domain(name="penplan-pddl")
        state = PlanState(set(self._initial_facts(scenario)))
        context = AgentContext(scenario=scenario, retrieved=retrieved_nodes)

        for agent in self.agents:
            steps = agent.plan(context, state.facts)
            for step in steps:
                plan.append(step)
                domain.add_action(_action_from_step(step))
                state.apply(step.effects)
            if len(plan) >= self.config.verification.max_plan_length:
                break

        problem = PlanningProblem(
            domain_name=domain.name,
            initial_state=self._initial_facts(scenario),
            goals=self._goal_facts(scenario),
            risk_budget=self.config.verification.allow_risk_budget,
        )

        validator = PlanValidator(domain, problem)
        report = validator.validate(plan)
        repairs = 0
        while not report.success and repairs < self.config.verification.max_repairs:
            repaired = False
            for issue in report.issues:
                if issue.missing_preconditions:
                    repaired = self.repairer.attempt_repair(plan, domain, issue)
                if repaired:
                    break
            if not repaired:
                break
            repairs += 1
            report = validator.validate(plan)

        context_ids = [node.node_id for node in retrieved_nodes]
        return PipelineResult(
            plan=plan,
            domain=domain,
            problem=problem,
            report=report,
            retrieved_context=context_ids,
        )

    def _initial_facts(self, scenario: Dict[str, Any]) -> set[str]:
        facts = set(scenario.get("initial_facts", []))
        facts.add("mission_received")
        facts.add("environment_profiled")
        return facts

    def _goal_facts(self, scenario: Dict[str, Any]) -> set[str]:
        goals = set(scenario.get("goal_facts", []))
        if not goals:
            goals.add("report_drafted")
        return goals

    def _scenario_to_query(self, scenario: Dict[str, Any]) -> str:
        return " ".join(
            [
                scenario.get("mission", ""),
                scenario.get("target_asset", ""),
                " ".join(scenario.get("threats", [])),
                " ".join(scenario.get("constraints", [])),
            ]
        ).strip()


def _action_from_step(step: PlanStep) -> ActionDefinition:
    return ActionDefinition(
        name=step.action_id,
        preconditions=set(step.preconditions),
        add_effects={effect for effect in step.effects if not effect.startswith("not ")},
        del_effects={effect[4:] for effect in step.effects if effect.startswith("not ")},
        cost=step.cost,
        risk=step.risk,
    )


__all__ = ["PenPlanPipeline", "PipelineResult"]
