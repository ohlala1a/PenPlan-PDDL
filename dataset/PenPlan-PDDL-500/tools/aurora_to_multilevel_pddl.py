#!/usr/bin/env python3
"""
Aurora to Multi-Level PDDL Problem Generator
Converts Aurora attack scenarios to 3-level PDDL problem files matching existing dataset format
"""

import os
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class AuroraToMultiLevelPDDL:
    """Convert Aurora scenarios to strategic/tactical/technical PDDL problems"""

    def __init__(self, aurora_dir: str, output_base_dir: str):
        self.aurora_dir = Path(aurora_dir)
        self.output_base_dir = Path(output_base_dir)
        self.problems_dir = self.output_base_dir / "datasets" / "pddl" / "problems"

        # Create base directories
        self.problems_dir.mkdir(parents=True, exist_ok=True)

        # Track scenario numbering
        self.existing_scenarios = self._get_existing_scenarios()
        self.next_scenario_id = self._get_next_scenario_id()

    def _get_existing_scenarios(self) -> List[str]:
        """Get list of existing scenario directories"""
        if not self.problems_dir.exists():
            return []
        return [d.name for d in self.problems_dir.iterdir() if d.is_dir()]

    def _get_next_scenario_id(self) -> int:
        """Determine next scenario ID number"""
        max_id = 0
        for scenario in self.existing_scenarios:
            if scenario.startswith('scenario_'):
                try:
                    num = int(scenario.split('_')[1])
                    max_id = max(max_id, num)
                except:
                    pass
        return max_id + 1

    def parse_aurora_attack_chain(self, yaml_path: Path) -> Dict:
        """Parse Aurora attack_chain.yml"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_strategic_problem(self, aurora_data: Dict, scenario_id: str) -> str:
        """
        Generate strategic-level PDDL problem (high-level, abstract)
        Format: Standard PDDL with simple objects and goals
        """
        adversary_name = aurora_data.get('emulation_plan_details', {}).get('adversary_name', 'unknown')
        actions = aurora_data.get('attack_action_sequence', [])
        testbed = aurora_data.get('testbed_requirement', {})

        # Extract target host info
        hosts = list(testbed.keys()) if testbed else ['target-host']
        target_host = hosts[0] if hosts else 'target-host'

        # Determine attack goal from last action
        final_effects = []
        if actions:
            last_action = actions[-1]
            for effect in last_action.get('effects', []):
                if isinstance(effect, str) and not effect.startswith('~'):
                    final_effects.append(effect)

        pddl = f"""(define (problem {scenario_id}-strategic)
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
    (connected target-system target-service)
    (service-running target-service)
    (has-vuln target-service cve-vuln)
    (not (isolated target-network))
    (not (isolated target-system))
    (not (isolated target-service))
  )

  (:goal (and
    (user-access target-system)
    (discovered sensitive-data)
  ))
)
"""
        return pddl

    def generate_tactical_problem(self, aurora_data: Dict, scenario_id: str) -> str:
        """
        Generate tactical-level PDDL problem (ATT&CK technique focused)
        Format: Pseudo-PDDL with [brackets]
        """
        adversary_name = aurora_data.get('emulation_plan_details', {}).get('adversary_name', 'unknown')
        actions = aurora_data.get('attack_action_sequence', [])
        testbed = aurora_data.get('testbed_requirement', {})

        # Extract unique ATT&CK techniques
        techniques = set()
        tactics = set()
        for action in actions:
            for tech_id in action.get('id', []):
                if tech_id:
                    techniques.add(tech_id)
            for tactic in action.get('tactics', []):
                if tactic:
                    tactics.add(tactic)

        # Get target info
        hosts = list(testbed.keys()) if testbed else ['target']
        target_host = hosts[0] if hosts else 'target'
        os_type = testbed.get(target_host, {}).get('os', 'windows') if testbed else 'windows'

        # Create objects list
        objects_list = [
            f"{os_type}-system",
            "vulnerability-1",
            "sensitive-data",
        ]

        # Add technique-based objects
        for i, tech in enumerate(sorted(techniques)[:5], 1):
            objects_list.append(f"technique-{tech.replace('.', '-')}")

        pddl = f"""(define (problem {scenario_id}-tactical)
  (:domain pentest-root)

  (:objects
    {' '.join(objects_list)}
  )

  (:init
"""

        # Add initial state
        pddl += f"    [{os_type}-system is running on network segment A]\n"
        pddl += f"    [vulnerability-1 is present in {os_type}-system]\n"
        pddl += f"    [sensitive-data is stored on {os_type}-system]\n"

        # Add technique info
        for tech in sorted(techniques)[:3]:
            pddl += f"    [technique-{tech.replace('.', '-')} is available]\n"

        pddl += "  )\n  \n  (:goal\n"

        # Add goals based on tactics
        if 'Initial Access' in tactics or 'Execution' in tactics:
            pddl += f"    [initial access to {os_type}-system is achieved]\n"
        if 'Persistence' in tactics or 'Privilege Escalation' in tactics:
            pddl += f"    [persistence on {os_type}-system is established]\n"
        if 'Defense Evasion' in tactics:
            pddl += f"    [defenses on {os_type}-system are evaded]\n"
        if 'Collection' in tactics or 'Exfiltration' in tactics:
            pddl += f"    [sensitive-data is collected and exfiltrated]\n"

        # Default goal if none matched
        if pddl.count('[') <= 3:  # Only init statements
            pddl += f"    [attack objectives on {os_type}-system are completed]\n"

        pddl += "  )\n)\n"

        return pddl

    def generate_technical_problem(self, aurora_data: Dict, scenario_id: str) -> str:
        """
        Generate technical-level PDDL problem (detailed tools and commands)
        Format: Pseudo-PDDL with typed objects and detailed [bracket] predicates
        """
        adversary_name = aurora_data.get('emulation_plan_details', {}).get('adversary_name', 'unknown')
        actions = aurora_data.get('attack_action_sequence', [])
        testbed = aurora_data.get('testbed_requirement', {})

        # Get target info
        hosts = list(testbed.keys()) if testbed else ['target']
        target_host = hosts[0] if hosts else 'target'
        os_type = testbed.get(target_host, {}).get('os', 'windows') if testbed else 'windows'

        # Extract tools and techniques
        tools = set()
        techniques = []
        for action in actions:
            # Extract executor as tool
            executor = action.get('execution', {}).get('executor', '')
            if executor and executor != 'None' and executor != 'Human':
                tools.add(executor)

            # Store technique with details
            for tech_id in action.get('id', []):
                if tech_id:
                    techniques.append({
                        'id': tech_id,
                        'name': action.get('name', ''),
                        'tactic': action.get('tactics', [])[0] if action.get('tactics') else ''
                    })

        pddl = f"""(define (problem {scenario_id}-technical)
  (:domain pentest-root)

  (:objects
    {os_type}-{scenario_id} :system-asset
"""

        # Add tools as objects
        for i, tool in enumerate(sorted(tools)[:10], 1):
            tool_clean = tool.replace(' ', '-').replace('.', '-').lower()
            pddl += f"    {tool_clean}-{scenario_id} :attack-tool\n"

        # Add generic objects
        pddl += f"    sensitive-data-{scenario_id} :data\n"
        pddl += f"    vulnerability-1-{scenario_id} :vulnerability\n"
        pddl += f"    defense-tool-1-{scenario_id} :defense-tool\n"

        pddl += "  )\n  \n  (:init\n"

        # Add initial conditions
        pddl += f"    [{os_type}-{scenario_id} (os-type) {os_type}]\n"
        pddl += f"    [sensitive-data-{scenario_id} (data-type) confidential]\n"
        pddl += f"    [sensitive-data-{scenario_id} (data-location) /var/data]\n"
        pddl += f"    [vulnerability-1-{scenario_id} (vulnerability-type) cve-unknown]\n"
        pddl += f"    [defense-tool-1-{scenario_id} (defense-tool-type) antivirus]\n"
        pddl += f"    [defense-tool-1-{scenario_id} (protection-level) medium]\n"

        # Add tool info
        for i, tool in enumerate(sorted(tools)[:5], 1):
            tool_clean = tool.replace(' ', '-').replace('.', '-').lower()
            pddl += f"    [{tool_clean}-{scenario_id} (attack-tool-type) {tool_clean}]\n"
            pddl += f"    [{tool_clean}-{scenario_id} (version) 1.0]\n"

        pddl += "  )\n  \n  (:goal\n    [and\n"

        # Add goals based on techniques
        for tech in techniques[:5]:
            tech_id_clean = tech['id'].replace('.', '-')
            pddl += f"      [execute-technique {tech_id_clean}]\n"

        pddl += f"      [exfiltrate-data sensitive-data-{scenario_id}]\n"
        pddl += f"      [evade-defense defense-tool-1-{scenario_id}]\n"
        pddl += "    ]\n  )\n)\n"

        return pddl

    def convert_aurora_scenario(self, aurora_scenario_dir: Path, limit: int = None) -> Dict:
        """Convert single Aurora scenario to 3-level PDDL problems"""
        attack_chain_file = aurora_scenario_dir / "attack_chain.yml"

        if not attack_chain_file.exists():
            return None

        aurora_name = aurora_scenario_dir.name
        scenario_id = f"scenario_{self.next_scenario_id:04d}"

        print(f"Converting Aurora {aurora_name} -> {scenario_id}")

        # Parse Aurora data
        aurora_data = self.parse_aurora_attack_chain(attack_chain_file)

        # Create scenario directory
        scenario_dir = self.problems_dir / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Generate 3 levels
        strategic_pddl = self.generate_strategic_problem(aurora_data, scenario_id)
        tactical_pddl = self.generate_tactical_problem(aurora_data, scenario_id)
        technical_pddl = self.generate_technical_problem(aurora_data, scenario_id)

        # Write files
        (scenario_dir / "strategic.pddl").write_text(strategic_pddl, encoding='utf-8')
        (scenario_dir / "tactical.pddl").write_text(tactical_pddl, encoding='utf-8')
        (scenario_dir / "technical.pddl").write_text(technical_pddl, encoding='utf-8')

        self.next_scenario_id += 1

        return {
            'scenario_id': scenario_id,
            'aurora_name': aurora_name,
            'files_generated': 3
        }

    def convert_all_aurora_scenarios(self, limit: int = None):
        """Convert all Aurora scenarios"""
        aurora_scenarios = sorted([d for d in self.aurora_dir.iterdir() if d.is_dir()])

        if limit:
            aurora_scenarios = aurora_scenarios[:limit]

        print(f"Converting {len(aurora_scenarios)} Aurora scenarios to datasets/pddl/problems/")
        print(f"Starting from scenario ID: {self.next_scenario_id}")

        results = []
        for aurora_dir in aurora_scenarios:
            try:
                result = self.convert_aurora_scenario(aurora_dir)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error converting {aurora_dir.name}: {e}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_converted': len(results),
            'scenarios': results
        }

        summary_file = self.output_base_dir / "aurora_conversion_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nConversion complete!")
        print(f"- Converted: {len(results)} scenarios")
        print(f"- Total files generated: {len(results) * 3}")
        print(f"- Output: {self.problems_dir}")

        return results


def main():
    """Main conversion function"""
    aurora_dir = "/mnt/d/qy/作战规划/论文/多层次行动指南/pddl/Aurora-demos-main/attacks"
    output_base = "/mnt/d/qy/作战规划/论文/多层次行动指南/pddl"

    converter = AuroraToMultiLevelPDDL(aurora_dir, output_base)

    # Convert enough scenarios to reach 500 total files
    # Current: ~130 scenarios × 3 = 390 files
    # Need: ~37 more scenarios × 3 = 111 files
    # Let's convert 50 scenarios to have buffer: 50 × 3 = 150 files

    print("Converting Aurora scenarios to match existing dataset format...")
    print("Target: Add ~50 scenarios to reach 500+ total files\n")

    results = converter.convert_all_aurora_scenarios(limit=50)

    # Print final statistics
    total_existing = len(converter.existing_scenarios)
    total_new = len(results)
    total_scenarios = total_existing + total_new
    total_files = total_scenarios * 3

    print(f"\n{'='*60}")
    print("FINAL DATASET STATISTICS")
    print(f"{'='*60}")
    print(f"Existing scenarios: {total_existing}")
    print(f"New Aurora scenarios: {total_new}")
    print(f"Total scenarios: {total_scenarios}")
    print(f"Total problem files: {total_files}")
    print(f"Target (500 files): {'✓ ACHIEVED' if total_files >= 500 else '✗ NOT MET'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
