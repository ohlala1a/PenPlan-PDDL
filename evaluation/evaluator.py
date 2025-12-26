"""Evaluation framework for PenPlan-PDDL and baselines.

"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from pathlib import Path
import json
import csv
import time
from datetime import datetime

from .baselines import BaselineMethod, BaselineResult, get_baseline


@dataclass
class EvaluationMetrics:
    """Metrics for evaluation."""
    recall: float  # ATT&CK technique recall rate
    solvability: float  # Percentage with feasible plans
    avg_time: float  # Average planning time (seconds)
    command_accuracy: float = 0.0  # Command accuracy (CVE-Bench only)
    tool_calls: float = 0.0  # Average tool invocations (CVE-Bench only)
    first_success: float = 0.0  # First-attempt success rate (CVE-Bench only)


class AuroraEvaluator:
    """Evaluator for AURORA dataset (planning efficacy).

    AURORA dataset characteristics (from paper Section 3.1):
    - 327 techniques across 14 tactics
    - Large technique space for measuring recall
    """

    def __init__(self, dataset_path: str, output_dir: str):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_baseline(
        self,
        method: BaselineMethod,
        random_seed: int = 42
    ) -> EvaluationMetrics:
        """Evaluate baseline method on AURORA.

        Args:
            method: Baseline method to evaluate
            random_seed: Fixed random seed for reproducibility

        Returns:
            EvaluationMetrics with planning efficacy results
        """
        print(f"Evaluating {method.name} on AURORA dataset...")

        # Load scenarios (simplified - actual implementation would load from dataset)
        scenarios = self._load_aurora_scenarios()

        results: List[BaselineResult] = []
        total_recall = 0.0
        total_solvable = 0
        total_time = 0.0

        for i, scenario in enumerate(scenarios):
            print(f"  [{i+1}/{len(scenarios)}] Processing scenario {scenario.get('id', i)}...")

            result = method.plan(scenario)
            results.append(result)

            total_recall += result.recall
            if result.solvability:
                total_solvable += 1
            total_time += result.time_seconds

        # Calculate aggregate metrics
        num_scenarios = len(scenarios)
        metrics = EvaluationMetrics(
            recall=total_recall / num_scenarios if num_scenarios > 0 else 0.0,
            solvability=total_solvable / num_scenarios if num_scenarios > 0 else 0.0,
            avg_time=total_time / num_scenarios if num_scenarios > 0 else 0.0
        )

        # Save results
        self._save_results(method.name, results, metrics, "aurora")

        return metrics

    def _load_aurora_scenarios(self) -> List[Dict[str, Any]]:
        """Load AURORA scenarios.

        Returns placeholder scenarios for demonstration.
        Actual implementation would load from dataset files.
        """
        # Placeholder - generate sample scenarios
        return [{"id": f"aurora_{i:04d}", "target": f"target_{i}"} for i in range(100)]

    def _save_results(
        self,
        method_name: str,
        results: List[BaselineResult],
        metrics: EvaluationMetrics,
        dataset: str
    ):
        """Save evaluation results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed results as JSON
        json_file = self.output_dir / f"{dataset}_{method_name}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "method": method_name,
                "dataset": dataset,
                "timestamp": timestamp,
                "metrics": asdict(metrics),
                "results": [asdict(r) for r in results]
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved results to {json_file}")


class CVEBenchEvaluator:
    """Evaluator for CVE-Bench dataset (execution robustness).

    CVE-Bench characteristics:
    - Real-world vulnerability scenarios
    - End-to-end execution testing
    - Measures First success rate, Command Accuracy, Tool Calls
    """

    def __init__(self, dataset_path: str, output_dir: str):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_baseline(
        self,
        method: BaselineMethod,
        random_seed: int = 42
    ) -> EvaluationMetrics:
        """Evaluate baseline method on CVE-Bench.

        Args:
            method: Baseline method to evaluate
            random_seed: Fixed random seed

        Returns:
            EvaluationMetrics with execution robustness results
        """
        print(f"Evaluating {method.name} on CVE-Bench dataset...")

        scenarios = self._load_cvebench_scenarios()

        results: List[BaselineResult] = []
        total_recall = 0.0
        total_solvable = 0
        total_time = 0.0
        total_ca = 0.0
        total_tool_calls = 0.0
        total_first_success = 0

        for i, scenario in enumerate(scenarios):
            print(f"  [{i+1}/{len(scenarios)}] Processing CVE {scenario.get('cve_id', i)}...")

            result = method.plan(scenario)
            results.append(result)

            total_recall += result.recall
            if result.solvability:
                total_solvable += 1
            total_time += result.time_seconds
            total_ca += result.command_accuracy
            total_tool_calls += result.tool_calls
            if result.success:
                total_first_success += 1

        # Calculate aggregate metrics
        num_scenarios = len(scenarios)
        metrics = EvaluationMetrics(
            recall=total_recall / num_scenarios if num_scenarios > 0 else 0.0,
            solvability=total_solvable / num_scenarios if num_scenarios > 0 else 0.0,
            avg_time=total_time / num_scenarios if num_scenarios > 0 else 0.0,
            command_accuracy=total_ca / num_scenarios if num_scenarios > 0 else 0.0,
            tool_calls=total_tool_calls / num_scenarios if num_scenarios > 0 else 0.0,
            first_success=total_first_success / num_scenarios if num_scenarios > 0 else 0.0
        )

        # Save results
        self._save_results(method.name, results, metrics, "cvebench")

        return metrics

    def _load_cvebench_scenarios(self) -> List[Dict[str, Any]]:
        """Load CVE-Bench scenarios."""
        # Placeholder - generate sample CVE scenarios
        return [{"cve_id": f"CVE-2024-{i:05d}", "target": f"target_{i}"} for i in range(40)]

    def _save_results(
        self,
        method_name: str,
        results: List[BaselineResult],
        metrics: EvaluationMetrics,
        dataset: str
    ):
        """Save evaluation results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save as JSON
        json_file = self.output_dir / f"{dataset}_{method_name}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "method": method_name,
                "dataset": dataset,
                "timestamp": timestamp,
                "metrics": asdict(metrics),
                "results": [asdict(r) for r in results]
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved results to {json_file}")


def run_full_evaluation(
    baselines: List[str],
    aurora_path: str,
    cvebench_path: str,
    output_dir: str,
    random_seed: int = 42
):
    """Run full evaluation on both datasets.

    Args:
        baselines: List of baseline names to evaluate
        aurora_path: Path to AURORA dataset
        cvebench_path: Path to CVE-Bench dataset
        output_dir: Output directory for results
        random_seed: Fixed random seed (default 42, as per rebuttal)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize evaluators
    aurora_eval = AuroraEvaluator(aurora_path, output_path / "aurora")
    cvebench_eval = CVEBenchEvaluator(cvebench_path, output_path / "cvebench")

    # Results summary
    summary = {
        "aurora": {},
        "cvebench": {},
        "timestamp": datetime.now().isoformat(),
        "random_seed": random_seed
    }

    for baseline_name in baselines:
        print(f"\n{'='*60}")
        print(f"Evaluating baseline: {baseline_name}")
        print(f"{'='*60}\n")

        # Get baseline instance with fixed seed
        baseline = get_baseline(baseline_name, random_seed=random_seed)

        # Evaluate on AURORA
        aurora_metrics = aurora_eval.evaluate_baseline(baseline, random_seed)
        summary["aurora"][baseline_name] = asdict(aurora_metrics)

        print(f"\nAURORA Results for {baseline_name}:")
        print(f"  Recall: {aurora_metrics.recall*100:.1f}%")
        print(f"  Solvability: {aurora_metrics.solvability*100:.1f}%")
        print(f"  Avg Time: {aurora_metrics.avg_time:.1f}s")

        # Evaluate on CVE-Bench
        cvebench_metrics = cvebench_eval.evaluate_baseline(baseline, random_seed)
        summary["cvebench"][baseline_name] = asdict(cvebench_metrics)

        print(f"\nCVE-Bench Results for {baseline_name}:")
        print(f"  First Success: {cvebench_metrics.first_success*100:.1f}%")
        print(f"  Command Accuracy: {cvebench_metrics.command_accuracy*100:.1f}%")
        print(f"  Tool Calls: {cvebench_metrics.tool_calls:.1f}")
        print(f"  Solvability: {cvebench_metrics.solvability*100:.1f}%")

    # Save overall summary
    summary_file = output_path / f"evaluation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Evaluation complete! Summary saved to: {summary_file}")
    print(f"{'='*60}")


__all__ = [
    "AuroraEvaluator",
    "CVEBenchEvaluator",
    "EvaluationMetrics",
    "run_full_evaluation",
]
