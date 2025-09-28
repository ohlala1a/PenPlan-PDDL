"""Configuration objects for the PenPlan-PDDL release pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RetrievalConfig:
    """Parameters controlling knowledge graph retrieval."""

    top_k: int = 8
    semantic_weight: float = 0.7
    structural_weight: float = 0.3
    similarity_threshold: float = 0.32


@dataclass
class VerificationConfig:
    """Parameters for PDDL validation and repair."""

    max_repairs: int = 2
    allow_risk_budget: float = 0.55
    max_plan_length: int = 32


@dataclass
class RoleConfig:
    """Definition for each agent role participating in planning."""

    name: str
    layer: str
    weight: float
    objectives: List[str] = field(default_factory=list)


@dataclass
class PenPlanConfig:
    """Aggregate configuration for the PenPlan-PDDL pipeline."""

    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    roles: List[RoleConfig] = field(
        default_factory=lambda: [
            RoleConfig("Manager", "strategic", 0.22, ["identify mission goals", "map constraints"]),
            RoleConfig("Commander", "strategic", 0.2, ["sequence objectives", "assign tactics"]),
            RoleConfig("Reconnaissance", "tactical", 0.12, ["collect intelligence", "prepare entry"]),
            RoleConfig("SocialEngineer", "tactical", 0.08, ["craft initial access vectors"]),
            RoleConfig("Opsec", "tactical", 0.08, ["minimize detection", "ensure stealth"]),
            RoleConfig("Purple", "tactical", 0.08, ["align offensive and defensive insights"]),
            RoleConfig("Exploiter", "technical", 0.08, ["execute exploits", "obtain foothold"]),
            RoleConfig("PostExploitation", "technical", 0.05, ["escalate privileges", "harvest data"]),
            RoleConfig("Infrastructure", "technical", 0.03, ["maintain C2", "deploy tooling"]),
            RoleConfig("Cloud", "technical", 0.03, ["handle cloud assets", "maintain persistence"]),
            RoleConfig("Reporter", "technical", 0.01, ["summarize outcomes", "prepare debrief"]),
        ]
    )
    random_seed: int = 1337


__all__ = [
    "PenPlanConfig",
    "RetrievalConfig",
    "VerificationConfig",
    "RoleConfig",
]
