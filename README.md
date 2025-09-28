# PenPlan-PDDL Public Release

PenPlan-PDDL is a lightweight code release that accompanies the paper
*PenPlan-PDDL: A Multi-Agent Framework for Automated Penetration Testing Planning with PDDL-Based Verification*.
It focuses on providing a clear, reproducible coding reference for the
multi-layer planning pipeline, knowledge-enabled retrieval, and PDDL verification loop
introduced in the manuscript.

## Features

- **Hierarchical multi-agent planner** that organizes eleven operational roles across strategic, tactical, and technical layers.
- **Knowledge graph retrieval** using hashing-based embeddings that balance semantic similarity with structural coverage.
- **PDDL-style verification loop** that validates plans against logical preconditions, risk budgets, and goal reachability.
- **Constrained repair mechanism** capable of injecting minimal corrective actions when validation highlights missing prerequisites.
- **Self-contained demo scenario** and CLI for running the pipeline without external services or additional tool installations.

## Project Layout

```
penplan_pddl/
  __init__.py           # Package entrée
  config.py             # Tunable configuration dataclasses
  pipeline.py           # Orchestrates retrieval, planning, and verification
  knowledge_graph.py    # Lightweight ATT&CK-inspired knowledge graph
  agents/               # Role implementations for each planning layer
  plan/                 # Planning primitives (PlanStep, Plan, etc.)
  pddl/                 # Domain, problem, validation, and repair utilities
  data/knowledge_graph.json   # Sample knowledge graph used for retrieval
scenarios/example_scenario.json  # Demonstration scenario file
tests/test_pipeline.py            # Regression check for the pipeline flow
pyproject.toml                    # Packaging metadata
```

## Installation

The code targets Python 3.9+ and depends only on the Python standard library.
To install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Quick Start

Run the included scenario through the pipeline:

```bash
python -m penplan_pddl.cli
```

The CLI prints the retrieved knowledge graph context, the layered plan, and the
result of PDDL verification. A non-zero exit code indicates that validation failed.

## Programmatic Usage

```python
from penplan_pddl import PenPlanConfig, PenPlanPipeline
import json

scenario = json.loads(open("scenarios/example_scenario.json", "r", encoding="utf-8").read())
pipeline = PenPlanPipeline(PenPlanConfig())
result = pipeline.plan(scenario)

for step in result.plan.steps:
    print(step.action_id, step.effects)

assert result.report.success
```

## Testing

The repository ships with a lightweight regression test:

```bash
pytest
```

The test ensures the generated plan complies with validation and stays within the
configured plan length budget.

## License

This release is distributed under the MIT License. See `pyproject.toml` for details.
