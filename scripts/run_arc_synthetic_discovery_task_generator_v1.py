#!/usr/bin/env python3
"""Run the ARC-AGI-2 synthetic discovery task generator and evaluator.

Synthetic-only: no public ARC data, no scoring, no submission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_discovery_task_corpus_v1, summarize_synthetic_task_corpus_v1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ARC-AGI2 synthetic discovery task generator V1")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--tasks-per-family", type=int, default=1)
    parser.add_argument("--include-adversarial", action="store_true")
    parser.add_argument("--include-compositions", action="store_true")
    parser.add_argument("--max-grid-size", type=int, default=6)
    parser.add_argument("--min-train-pairs", type=int, default=1)
    parser.add_argument("--max-train-pairs", type=int, default=2)
    args = parser.parse_args()

    tasks = build_arc_synthetic_discovery_task_corpus_v1(
        seed=args.seed,
        tasks_per_family=args.tasks_per_family,
        include_adversarial=args.include_adversarial,
        include_compositions=args.include_compositions,
        max_grid_size=args.max_grid_size,
        min_train_pairs=args.min_train_pairs,
        max_train_pairs=args.max_train_pairs,
    )
    report = evaluate_arc_synthetic_discovery_tasks_v1(tasks).to_json_safe_dict()
    payload = {
        "generator_summary": summarize_synthetic_task_corpus_v1(tasks),
        "evaluation_report": report,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
