"""PenPlan-PDDL public release package.

This package implements a lightweight version of the PenPlan-PDDL
pipeline described in the accompanying paper. It focuses on the
planning and verification flow rather than full execution automation."""

from .config import PenPlanConfig
from .pipeline import PenPlanPipeline

__all__ = ["PenPlanConfig", "PenPlanPipeline"]
__version__ = "0.1.0"
