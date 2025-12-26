#!/usr/bin/env python3
"""Run baseline comparisons for PenPlan-PDDL paper.

Usage:
    python scripts/run_evaluation.py --dataset aurora --baselines all
    python scripts/run_evaluation.py --dataset cvebench --baselines T-Agent,AutoGPT
    python scripts/run_evaluation.py --dataset all --output results/

"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation import run_full_evaluation, get_baseline, AuroraEvaluator, CVEBenchEvaluator


def main():
    parser = argparse.ArgumentParser(
        description="Run PenPlan-PDDL baseline evaluations"
    )

    parser.add_argument(
        "--dataset",
        choices=["aurora", "cvebench", "all"],
        default="all",
        help="Dataset to evaluate on (default: all)"
    )

    parser.add_argument(
        "--baselines",
        type=str,
        default="all",
        help="Comma-separated baseline names or 'all' (default: all)"
    )

    parser.add_argument(
        "--aurora-path",
        type=str,
        default="dataset/aurora",
        help="Path to AURORA dataset (default: dataset/aurora)"
    )

    parser.add_argument(
        "--cvebench-path",
        type=str,
        default="dataset/cvebench",
        help="Path to CVE-Bench dataset (default: dataset/cvebench)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_results",
        help="Output directory (default: evaluation_results)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    # Parse baseline names
    if args.baselines.lower() == "all":
        baseline_names = ["AutoGPT", "PentestGPT", "CyAgent", "T-Agent", "Rule-Based"]
    else:
        baseline_names = [b.strip() for b in args.baselines.split(",")]

    print("="*70)
    print("PenPlan-PDDL Baseline Evaluation")
    print("="*70)
    print(f"Dataset(s): {args.dataset}")
    print(f"Baselines: {', '.join(baseline_names)}")
    print(f"Random seed: {args.seed}")
    print(f"Output directory: {args.output}")
    print("="*70)
    print()

    # Run evaluations
    if args.dataset == "all":
        run_full_evaluation(
            baselines=baseline_names,
            aurora_path=args.aurora_path,
            cvebench_path=args.cvebench_path,
            output_dir=args.output,
            random_seed=args.seed
        )
    elif args.dataset == "aurora":
        evaluator = AuroraEvaluator(args.aurora_path, Path(args.output) / "aurora")
        for baseline_name in baseline_names:
            baseline = get_baseline(baseline_name, args.seed)
            metrics = evaluator.evaluate_baseline(baseline, args.seed)
            print(f"\n{baseline_name} AURORA Results:")
            print(f"  Recall: {metrics.recall*100:.1f}%")
            print(f"  Solvability: {metrics.solvability*100:.1f}%")
            print(f"  Avg Time: {metrics.avg_time:.1f}s")
    elif args.dataset == "cvebench":
        evaluator = CVEBenchEvaluator(args.cvebench_path, Path(args.output) / "cvebench")
        for baseline_name in baseline_names:
            baseline = get_baseline(baseline_name, args.seed)
            metrics = evaluator.evaluate_baseline(baseline, args.seed)
            print(f"\n{baseline_name} CVE-Bench Results:")
            print(f"  First Success: {metrics.first_success*100:.1f}%")
            print(f"  Command Accuracy: {metrics.command_accuracy*100:.1f}%")
            print(f"  Tool Calls: {metrics.tool_calls:.1f}")
            print(f"  Solvability: {metrics.solvability*100:.1f}%")

    print("\n" + "="*70)
    print("Evaluation complete!")
    print("="*70)


if __name__ == "__main__":
    main()
