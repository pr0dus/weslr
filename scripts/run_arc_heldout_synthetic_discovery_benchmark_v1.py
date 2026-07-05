#!/usr/bin/env python3
"""Run the ARC-AGI-2 held-out synthetic discovery benchmark V1.

Synthetic-only benchmark runner: no public ARC data, no scoring submission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weslr.arc_heldout_synthetic_discovery_benchmark_v1 import build_heldout_synthetic_discovery_benchmark_v1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ARC-AGI-2 held-out synthetic discovery benchmark V1")
    parser.add_argument("--dev-seed", type=int, default=2435)
    parser.add_argument("--heldout-seed", type=int, default=82435)
    parser.add_argument("--tasks-per-family-dev", type=int, default=3)
    parser.add_argument("--tasks-per-family-heldout", type=int, default=5)
    parser.add_argument("--include-adversarial", action="store_true")
    parser.add_argument("--include-compositions", action="store_true")
    args = parser.parse_args()

    payload = build_heldout_synthetic_discovery_benchmark_v1(
        dev_seed=args.dev_seed,
        heldout_seed=args.heldout_seed,
        tasks_per_family_dev=args.tasks_per_family_dev,
        tasks_per_family_heldout=args.tasks_per_family_heldout,
        include_adversarial=args.include_adversarial,
        include_compositions=args.include_compositions,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
