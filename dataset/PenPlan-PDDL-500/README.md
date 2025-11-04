# PenPlan-PDDL-500

## Multi-Level Penetration Testing Planning Domain Definition Language Dataset


---

## Overview

PenPlan-PDDL-500 is a comprehensive PDDL (Planning Domain Definition Language) dataset for penetration testing scenarios, designed to support automated cybersecurity planning, attack path analysis, and defensive security research. This dataset provides multi-level abstraction of penetration testing operations, enabling automated reasoning about attack strategies at strategic, tactical, and technical levels.

### Key Features

- **Multi-Level Abstraction**: Each scenario is represented at three levels:
  - **Strategic**: High-level business objectives and abstract attack goals
  - **Tactical**: MITRE ATT&CK technique-focused operations
  - **Technical**: Tool-specific implementation details

- **Comprehensive Coverage**: 181 penetration testing scenarios covering diverse attack vectors, targets, and techniques

- **Standardized Format**: Unified domain (`pentest-root`) with consistent predicate and action definitions

- **Solving Metadata**: Complete solving statistics, plan lengths, and performance metrics

- **Source Diversity**: Combines manually crafted scenarios with Aurora attack demonstration framework data

---

## Dataset Structure

```
PenPlan-PDDL-500/
├── README.md                          # This file
├── LICENSE                            # Dataset license
├── CITATION.cff                       # Citation information
│
├── domains/                           # Domain definition files
│   ├── pentest-root-domain.pddl      # Main unified domain
│   ├── network-subdomain.pddl        # Network-level operations (if applicable)
│   ├── system-subdomain.pddl         # System-level operations (if applicable)
│   └── service-subdomain.pddl        # Service-level operations (if applicable)
│
├── problems/                          # Problem definition files (181 scenarios)
│   ├── scenario_0001/
│   │   ├── strategic.pddl            # Strategic-level problem
│   │   ├── tactical.pddl             # Tactical-level problem
│   │   └── technical.pddl            # Technical-level problem
│   ├── scenario_0002/
│   │   └── ...
│   ├── ...
│   └── scenario_1364/                # Last Aurora-derived scenario
│       └── ...
│
├── metadata/                          # Dataset metadata and statistics
│   ├── pddl_solving_results_*.csv    # Solving results (CSV format)
│   ├── pddl_solving_results_*.json   # Complete solving results with plans
│   └── statistics_*.json             # Dataset statistics
│
└──  solvers/                           # PDDL solving tools
     └── batch_pddl_solver_mcp.py      # MCP-based batch solver

```

---

## PDDL Format Specifications

### Domain: `pentest-root`

The unified domain defines:

- **Types**: Asset hierarchy (network-asset, system-asset, service-asset, data, vulnerability)
- **Predicates**: Connectivity, access, isolation, discovery, exploitation
- **Actions**: Network operations, system exploitation, data collection, defense evasion

### Problem Files

Each scenario contains three problem files:

#### 1. Strategic Level (`strategic.pddl`)

**Format**: Standard PDDL 2.1 syntax

**Characteristics**:
- High-level abstract objects (attacker, target-network, target-system, sensitive-data)
- Business-oriented goals (user-access, data discovery, exfiltration)
- Simplified state representation

**Example**:
```pddl
(define (problem scenario_0001-strategic)
  (:domain pentest-root)

  (:objects
    attacker - asset
    target-network - network-asset
    target-system - system-asset
    target-service - service-asset
    sensitive-data - data
    cve-vuln - vulnerability
  )

  (:init
    (connected attacker target-network)
    (connected target-network target-system)
    (service-running target-service)
    (has-vuln target-service cve-vuln)
  )

  (:goal (and
    (user-access target-system)
    (discovered sensitive-data)
    (exfiltrated sensitive-data)
  ))
)
```

#### 2. Tactical Level (`tactical.pddl`)

**Format**: Pseudo-PDDL with bracket notation `[predicate]`

**Characteristics**:
- MITRE ATT&CK technique references (e.g., T1059-001, T1053-005)
- Tactic-based goals (Initial Access, Persistence, Defense Evasion)
- Specific system and vulnerability identification

**Example**:
```pddl
(define (problem scenario_0001-tactical)
  (:domain pentest-root)

  (:objects
    windows-system vulnerability-1 sensitive-data
    technique-T1005 technique-T1053-005 technique-T1059-001
  )

  (:init
    [windows-system is running on network segment A]
    [vulnerability-1 is present in windows-system]
    [technique-T1059-001 is available]
  )

  (:goal
    [initial access to windows-system is achieved]
    [persistence on windows-system is established]
    [sensitive-data is collected and exfiltrated]
  )
)
```

#### 3. Technical Level (`technical.pddl`)

**Format**: Pseudo-PDDL with typed objects and detailed bracket predicates

**Characteristics**:
- Specific tools and executors (powershell, cmd, mimikatz)
- Detailed system properties (OS type, versions, paths)
- Tool-specific goals and implementation details

**Example**:
```pddl
(define (problem scenario_0001-technical)
  (:domain pentest-root)

  (:objects
    windows-0001 :system-asset
    powershell-0001 :attack-tool
    cmd-0001 :attack-tool
    sensitive-data-0001 :data
    vulnerability-1-0001 :vulnerability
  )

  (:init
    [windows-0001 (os-type) windows]
    [powershell-0001 (attack-tool-type) powershell]
    [powershell-0001 (version) 5.1]
    [sensitive-data-0001 (data-location) /var/data]
  )

  (:goal
    [and
      [execute-technique T1059-001]
      [exfiltrate-data sensitive-data-0001]
    ]
  )
)
```

---

## Dataset Statistics

### File Distribution

| Level | Total Files | Format Valid | Actual Solvability | Solvable Count |
|-------|------------|--------------|-------------------|----------------|
| Strategic | 181 | 100% | 99.45% | 180/181 |
| Tactical | 181 | 100% | 100.00% | 181/181 |
| Technical | 178 | 100% | 100.00% | 178/178 |
| **Total** | **540** | **100%** | **99.81%** | **539/540** |



### Dataset Quality

- **Format Validity**: 100% (all files are standard PDDL 2.1)
- **Encoding**: 100% UTF-8 (57 files fixed from mixed encodings)
- **Domain Completeness**: 100% (9 actions fully defined)
- **Verified Solvability**: 99.81% (539/540 files solvable with Fast Downward)
  - Strategic level: 99.45% (180/181)
  - Tactical level: 100.00% (181/181)
  - Technical level: 100.00% (178/178)

---

## Usage Guide

### Quick Start

1. **Load a scenario**:
```bash
# View strategic-level problem
cat problems/scenario_0001/strategic.pddl
```

2. **Solve with PDDL planner** (example with Fast Downward):
```bash
# Convert tactical problem to standard PDDL (replace brackets)
sed 's/\[/(/g; s/\]/)/g' problems/scenario_0001/tactical.pddl > tactical_fixed.pddl

# Solve with Fast Downward
fast-downward.py domains/pentest-root-domain.pddl tactical_fixed.pddl --search "astar(lmcut())"
```

3. **Batch processing**:
```bash
# Use provided solver
python solvers/batch_pddl_solver_mcp.py
```

### Using MCP PDDL Server

The dataset includes MCP-compatible solving tools:

```python
# Example: Solve using MCP PDDL server
from mcp_tools import generate_plan

task = {
  "domain": "pentest-root",
  "objects": {"robots": ["attacker"], "rooms": ["network", "system"]},
  "init": {"at": [["attacker", "network"]]},
  "goal": {"at": [["attacker", "system"]]}
}

result = generate_plan(task)
print(result["plan_text"])
```

---

## Research Applications

### 1. Automated Penetration Testing Planning

Use PDDL planners to generate attack sequences:
- Strategic planning for red team operations
- Tactical technique selection based on ATT&CK
- Technical tool orchestration

### 2. Defense Strategy Analysis

Analyze defensive measures by:
- Identifying critical paths in attack graphs
- Evaluating defense-in-depth effectiveness
- Simulating detection and response scenarios

### 3. Security Education

Educational applications:
- Teaching attack methodologies
- Demonstrating multi-level planning
- Hands-on PDDL and cybersecurity exercises

### 4. AI/LLM Training

Dataset suitable for:
- Training cybersecurity-focused language models
- Fine-tuning planning agents
- Benchmarking automated reasoning systems



---

## Citation

If you use this dataset in your research, please cite:

```bibtex
@dataset{penplan_pddl_500_2025,
  title={PenPlan-PDDL-500: A Multi-Level PDDL Dataset for Penetration Testing Planning},
  author={[Your Name/Organization]},
  year={2025},
  publisher={[Publisher/Repository]},
  version={1.0},
  url={[Dataset URL]}
}
```

---



## Disclaimer

**IMPORTANT**: This dataset is intended SOLELY for:
- Defensive cybersecurity research
- Security education and training
- Authorized penetration testing
- Academic research

**DO NOT**:
- Use for unauthorized access to systems
- Apply techniques against systems without explicit permission
- Use for malicious purposes

The authors and contributors are not responsible for misuse of this dataset.

---

## Acknowledgments

- **Aurora Attack Framework**: Source of 50 scenarios (https://github.com/mitrecorp/aurora)
- **MITRE ATT&CK**: Technique and tactic taxonomy
- **PDDL Community**: Planning domain definition language standards
- **Fast Downward**: Reference PDDL planner

---


## Future Work

Planned enhancements:
- [ ] Expand to 500+ scenarios
- [ ] Add more Aurora attack demonstrations
- [ ] Include domain variations for different environments
- [ ] Provide pre-computed solution plans
- [ ] Integration with automated planning tools
- [ ] Multi-language documentation

---

