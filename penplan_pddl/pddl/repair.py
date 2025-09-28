"""Constrained repair logic for PenPlan-PDDL plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional

from ..plan import Plan, PlanStep, ValidationIssue
from .domain import ActionDefinition, Domain


@dataclass
class RepairLibraryEntry:
    fact: str
    builder: Callable[[], PlanStep]


def _action_from_step(step: PlanStep) -> ActionDefinition:
    return ActionDefinition(
        name=step.action_id,
        preconditions=set(step.preconditions),
        add_effects={effect for effect in step.effects if not effect.startswith("not ")},
        del_effects={effect[4:] for effect in step.effects if effect.startswith("not ")},
        cost=step.cost,
        risk=step.risk,
    )


class PlanRepairer:
    """Injects lightweight corrective steps when validation fails."""

    def __init__(self) -> None:
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
            ),
        }

    def attempt_repair(
        self,
        plan: Plan,
        domain: Domain,
        issue: ValidationIssue,
    ) -> bool:
        for missing in issue.missing_preconditions:
            entry = self._library.get(missing)
            if entry is None:
                continue
            step = entry.builder()
            plan.insert(issue.index, step)
            domain.add_action(_action_from_step(step))
            return True
        return False


__all__ = ["PlanRepairer"]
