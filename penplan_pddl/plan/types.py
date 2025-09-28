"""Planning primitives used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set


@dataclass
class PlanStep:
    action_id: str
    description: str
    role: str
    layer: str
    preconditions: Set[str] = field(default_factory=set)
    effects: Set[str] = field(default_factory=set)
    cost: float = 1.0
    risk: float = 0.05


@dataclass
class PlanState:
    facts: Set[str]

    def apply(self, effects: Sequence[str]) -> None:
        for fact in effects:
            if fact.startswith("not "):
                self.facts.discard(fact[4:])
            else:
                self.facts.add(fact)


@dataclass
class Plan:
    steps: List[PlanStep] = field(default_factory=list)

    def append(self, step: PlanStep) -> None:
        self.steps.append(step)

    def insert(self, index: int, step: PlanStep) -> None:
        self.steps.insert(index, step)

    def __iter__(self):
        return iter(self.steps)

    def __len__(self) -> int:
        return len(self.steps)


@dataclass
class ValidationIssue:
    index: int
    step: PlanStep
    missing_preconditions: Set[str] = field(default_factory=set)
    exceeded_risk: bool = False


__all__ = ["Plan", "PlanState", "PlanStep", "ValidationIssue"]
