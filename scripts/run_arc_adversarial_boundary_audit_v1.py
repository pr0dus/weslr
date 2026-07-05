#!/usr/bin/env python3
"""Run the ARC-AGI-2 adversarial boundary audit V1.

Usage:
  python scripts/run_arc_adversarial_boundary_audit_v1.py \
    --dev-seed 2435 --heldout-seed 82435 \
    --tasks-per-family-dev 3 --tasks-per-family-heldout 5 \
    --include-adversarial --include-compositions
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root on path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from weslr.arc_heldout_synthetic_discovery_benchmark_v1 import build_heldout_synthetic_discovery_benchmark_v1
from weslr.arc_adversarial_boundary_audit_v1 import audit_adversarial_families_from_evaluation, audit_to_json


def main() -> int:
    parser = argparse.ArgumentParser(description="ARC-AGI-2 Adversarial Boundary Audit V1")
    parser.add_argument("--dev-seed", type=int, default=2435)
    parser.add_argument("--heldout-seed", type=int, default=82435)
    parser.add_argument("--tasks-per-family-dev", type=int, default=3)
    parser.add_argument("--tasks-per-family-heldout", type=int, default=5)
    parser.add_argument("--include-adversarial", action="store_true", default=True)
    parser.add_argument("--include-compositions", action="store_true", default=True)
    parser.add_argument("--output", type=str, default=None, help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    benchmark = build_heldout_synthetic_discovery_benchmark_v1(
        dev_seed=args.dev_seed,
        heldout_seed=args.heldout_seed,
        tasks_per_family_dev=args.tasks_per_family_dev,
        tasks_per_family_heldout=args.tasks_per_family_heldout,
        include_adversarial=args.include_adversarial,
        include_compositions=args.include_compositions,
    )

    dev_eval = benchmark["dev"]["evaluation"]
    heldout_eval = benchmark["heldout"]["evaluation"]
    dev_tasks = benchmark["dev"]["tasks"]
    heldout_tasks = benchmark["heldout"]["tasks"]

    dev_audit = audit_adversarial_families_from_evaluation(dev_eval, dev_tasks)
    heldout_audit = audit_adversarial_families_from_evaluation(heldout_eval, heldout_tasks)

    result = {
        "dev_audit": dev_audit,
        "heldout_audit": heldout_audit,
        "deterministic_replay_pass": benchmark.get("deterministic_replay_pass"),
        "split_disjoint_pass": benchmark.get("split_disjoint_pass"),
        "expected_output_isolation_pass": benchmark.get("expected_output_isolation_pass"),
    }

    output = json.dumps(result, indent=2, sort_keys=True, default=str)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Audit written to {args.output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())