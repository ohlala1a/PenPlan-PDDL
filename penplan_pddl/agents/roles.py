"""Role implementations used by the PenPlan-PDDL pipeline."""

from __future__ import annotations

from typing import Iterable, List, Optional

from ..knowledge_graph import GraphNode
from ..plan import PlanStep
from .base import AgentContext, RoleAgent


def _pick_by_tactic(nodes: Iterable[GraphNode], tactic_keyword: str) -> Optional[GraphNode]:
    tactic_keyword = tactic_keyword.lower()
    for node in nodes:
        if tactic_keyword in node.tactic.lower():
            return node
    return next(iter(nodes), None)


def _summarize(node: Optional[GraphNode]) -> str:
    if node is None:
        return ""
    return f"Selected technique: {node.name} ({node.tactic})."


class StrategicManager(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        mission = context.scenario.get("mission") or "Unnamed assessment"
        constraints = context.scenario.get("constraints", [])
        description = (
            f"Assess mission '{mission}' and encode constraints: {', '.join(constraints) or 'none'}."
        )
        step = self._make_step(
            action_id="analyze_mission",
            description=description,
            preconditions=["mission_received"],
            effects=["goals_established", "constraints_documented"],
            risk=0.01,
            cost=1.5,
        )
        return [step]


class StrategicCommander(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        priority_asset = context.scenario.get("target_asset", "critical system")
        description = f"Translate mission goals into campaign sequence focusing on {priority_asset}."
        step = self._make_step(
            action_id="shape_campaign",
            description=description,
            preconditions=["goals_established"],
            effects=["campaign_sequence_prepared", "targets_prioritized"],
            risk=0.02,
            cost=1.2,
        )
        return [step]


class ReconnaissanceAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        node = _pick_by_tactic(context.retrieved, "reconnaissance")
        description = (
            "Execute intelligence collection to map exposed services. "
            + _summarize(node)
        )
        step = self._make_step(
            action_id="collect_recon",
            description=description,
            preconditions=["campaign_sequence_prepared"],
            effects=["reconnaissance_intelligence_collected"],
            risk=0.04,
            cost=1.5,
        )
        return [step]


class SocialEngineerAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        node = _pick_by_tactic(context.retrieved, "initial access")
        description = (
            "Construct human-centric access vector informed by reconnaissance. "
            + _summarize(node)
        )
        step = self._make_step(
            action_id="craft_initial_access",
            description=description,
            preconditions=["reconnaissance_intelligence_collected"],
            effects=["initial_access_vector_prepared"],
            risk=0.06,
            cost=1.6,
        )
        return [step]


class OpsecAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        node = _pick_by_tactic(context.retrieved, "defense evasion")
        description = "Apply operational security controls before action. " + _summarize(node)
        step = self._make_step(
            action_id="establish_opsec",
            description=description,
            preconditions=["campaign_sequence_prepared"],
            effects=["opsec_measures_established"],
            risk=0.03,
            cost=1.0,
        )
        return [step]


class PurpleAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        description = (
            "Validate offensive plan with defensive insights to ensure coverage and stealth."
        )
        step = self._make_step(
            action_id="align_opsec",
            description=description,
            preconditions=["opsec_measures_established", "initial_access_vector_prepared"],
            effects=["joint_alignment_confirmed"],
            risk=0.02,
            cost=0.8,
        )
        return [step]


class ExploiterAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        node = _pick_by_tactic(context.retrieved, "execution")
        description = "Execute exploit chain to gain foothold. " + _summarize(node)
        step = self._make_step(
            action_id="execute_exploit",
            description=description,
            preconditions=["initial_access_vector_prepared", "opsec_measures_established"],
            effects=["access_obtained"],
            risk=0.08,
            cost=1.8,
        )
        return [step]


class PostExploitationAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        node = _pick_by_tactic(context.retrieved, "privilege escalation")
        description = "Elevate privileges and collect artifacts. " + _summarize(node)
        step = self._make_step(
            action_id="escalate_privileges",
            description=description,
            preconditions=["access_obtained"],
            effects=["privileges_escalated", "loot_collected"],
            risk=0.07,
            cost=1.7,
        )
        return [step]


class InfrastructureAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        description = "Stage resilient command-and-control infrastructure for sustained operations."
        step = self._make_step(
            action_id="stage_c2",
            description=description,
            preconditions=["access_obtained"],
            effects=["c2_channel_staged"],
            risk=0.05,
            cost=1.2,
        )
        return [step]


class CloudAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        description = "Maintain persistence across hybrid and cloud assets."
        step = self._make_step(
            action_id="maintain_cloud_persistence",
            description=description,
            preconditions=["access_obtained"],
            effects=["cloud_persistence_established"],
            risk=0.04,
            cost=1.3,
        )
        return [step]


class ReporterAgent(RoleAgent):
    def plan(self, context: AgentContext, known_facts) -> List[PlanStep]:
        summary_focus = context.scenario.get("report_focus", "impact and mitigations")
        description = f"Compile mission report emphasizing {summary_focus}."
        step = self._make_step(
            action_id="prepare_report",
            description=description,
            preconditions=["privileges_escalated", "joint_alignment_confirmed"],
            effects=["report_drafted"],
            risk=0.01,
            cost=0.6,
        )
        return [step]


ROLE_IMPLEMENTATIONS = {
    "Manager": StrategicManager,
    "Commander": StrategicCommander,
    "Reconnaissance": ReconnaissanceAgent,
    "SocialEngineer": SocialEngineerAgent,
    "Opsec": OpsecAgent,
    "Purple": PurpleAgent,
    "Exploiter": ExploiterAgent,
    "PostExploitation": PostExploitationAgent,
    "Infrastructure": InfrastructureAgent,
    "Cloud": CloudAgent,
    "Reporter": ReporterAgent,
}


__all__ = [
    "ROLE_IMPLEMENTATIONS",
    "StrategicManager",
    "StrategicCommander",
    "ReconnaissanceAgent",
    "SocialEngineerAgent",
    "OpsecAgent",
    "PurpleAgent",
    "ExploiterAgent",
    "PostExploitationAgent",
    "InfrastructureAgent",
    "CloudAgent",
    "ReporterAgent",
]
