"""Problem instance representation for validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set


@dataclass
class PlanningProblem:
    domain_name: str
    initial_state: Set[str]
    goals: Set[str]
    risk_budget: float = 0.35


__all__ = ["PlanningProblem"]
