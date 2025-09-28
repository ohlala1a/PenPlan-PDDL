"""Minimal PDDL-like domain abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Set


@dataclass
class ActionDefinition:
    name: str
    preconditions: Set[str]
    add_effects: Set[str]
    del_effects: Set[str]
    cost: float = 1.0
    risk: float = 0.05


@dataclass
class Domain:
    name: str
    actions: List[ActionDefinition] = field(default_factory=list)

    def add_action(self, action: ActionDefinition) -> None:
        self.actions.append(action)

    def find_action(self, name: str) -> ActionDefinition:
        for action in self.actions:
            if action.name == name:
                return action
        raise KeyError(f"Action '{name}' not defined in domain {self.name}")


__all__ = ["Domain", "ActionDefinition"]
