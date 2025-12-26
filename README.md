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

### Requirements

- Python 3.9+
- Fast-Downward planner (for PDDL solving)

### Quick Install

```bash
# Clone repository
git clone https://github.com/ohlala1a/PenPlan-PDDL.git
cd PenPlan-PDDL

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package
pip install -e .
```

### Install Fast-Downward (Required for PDDL Solving)

```bash
# Ubuntu/Debian
sudo apt-get install fast-downward

# Or build from source
git clone https://github.com/aibasel/downward.git
cd downward
./build.py
```


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


## License

This release is distributed under the MIT License. See `pyproject.toml` for details.
