"""Base classes for role agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from ..knowledge_graph import GraphNode
from ..plan import PlanStep


@dataclass
class AgentContext:
    """Shared context supplied to every planning agent."""

    scenario: Dict[str, Any]
    retrieved: Sequence[GraphNode]


class RoleAgent:
    """Base class that all role agents derive from."""

    def __init__(self, name: str, layer: str, weight: float, objectives: Iterable[str]):
        self.name = name
        self.layer = layer
        self.weight = weight
        self.objectives = list(objectives)

    def plan(self, context: AgentContext, known_facts: Iterable[str]) -> List[PlanStep]:
        raise NotImplementedError

    def _make_step(
        self,
        action_id: str,
        description: str,
        preconditions: Iterable[str],
        effects: Iterable[str],
        risk: float = 0.05,
        cost: float = 1.0,
    ) -> PlanStep:
        return PlanStep(
            action_id=action_id,
            description=description,
            role=self.name,
            layer=self.layer,
            preconditions=set(preconditions),
            effects=set(effects),
            risk=risk,
            cost=cost,
        )


__all__ = ["AgentContext", "RoleAgent"]
