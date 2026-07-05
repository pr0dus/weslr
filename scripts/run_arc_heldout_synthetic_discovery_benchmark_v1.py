#!/usr/bin/env python3
"""Run the ARC-AGI-2 held-out synthetic discovery benchmark V1.

Synthetic-only benchmark runner: no public ARC data, no scoring submission.
Supports optional structured event logging.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from weslr.arc_heldout_synthetic_discovery_benchmark_v1 import build_heldout_synthetic_discovery_benchmark_v1
from weslr.arc_run_event_log_v1 import ArcRunEventLogV1, make_run_id

DEFAULT_LOG_DIR = Path.home() / "weslr-arc-run-logs"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ARC-AGI-2 held-out synthetic discovery benchmark V1")
    parser.add_argument("--dev-seed", type=int, default=2435)
    parser.add_argument("--heldout-seed", type=int, default=82435)
    parser.add_argument("--tasks-per-family-dev", type=int, default=3)
    parser.add_argument("--tasks-per-family-heldout", type=int, default=5)
    parser.add_argument("--include-adversarial", action="store_true")
    parser.add_argument("--include-compositions", action="store_true")
    parser.add_argument("--include-diversified-families", action="store_true", help="Include diversified families")
    parser.add_argument("--diversified-tasks-per-family", type=int, default=3, help="Tasks per diversified family")
    parser.add_argument("--write-event-log", action="store_true", help="Write structured event log")
    parser.add_argument("--log-dir", type=str, default=str(DEFAULT_LOG_DIR), help="Log directory root")
    args = parser.parse_args()

    run_id = make_run_id()
    event_log: ArcRunEventLogV1 | None = None

    if args.write_event_log:
        log_dir = Path(args.log_dir) / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        event_log = ArcRunEventLogV1(run_id, log_dir)
        event_log.start_run({
            "dev_seed": args.dev_seed,
            "heldout_seed": args.heldout_seed,
            "tasks_per_family_dev": args.tasks_per_family_dev,
            "tasks_per_family_heldout": args.tasks_per_family_heldout,
            "include_adversarial": args.include_adversarial,
            "include_compositions": args.include_compositions,
            "include_diversified_families": args.include_diversified_families,
            "diversified_tasks_per_family": args.diversified_tasks_per_family,
        })

    payload = build_heldout_synthetic_discovery_benchmark_v1(
        dev_seed=args.dev_seed,
        heldout_seed=args.heldout_seed,
        tasks_per_family_dev=args.tasks_per_family_dev,
        tasks_per_family_heldout=args.tasks_per_family_heldout,
        include_adversarial=args.include_adversarial,
        include_compositions=args.include_compositions,
        include_diversified_families=args.include_diversified_families,
        diversified_tasks_per_family=args.diversified_tasks_per_family,
        event_log=event_log,
    )

    if event_log is not None:
        dev_summary = payload["dev"]["summary"]
        heldout_summary = payload["heldout"]["summary"]
        summary = {
            "dev": dev_summary,
            "heldout": heldout_summary,
            "deterministic_replay_pass": payload.get("deterministic_replay_pass"),
            "expected_output_isolation_pass": payload.get("expected_output_isolation_pass"),
            "split_disjoint_pass": payload.get("split_disjoint_pass"),
        }
        event_log.emit("SUMMARY", "run_summary", "run_summary",
                       "Benchmark run summary",
                       {
                           "dev_solved": dev_summary.get("solved_total", 0),
                           "dev_unsolved": dev_summary.get("unsolved_total", 0),
                           "dev_fallback_only": dev_summary.get("fallback_only", 0),
                           "dev_adversarial_rejection_pass": dev_summary.get("adversarial_rejection_pass", 0),
                           "dev_adversarial_rejection_fail": dev_summary.get("adversarial_rejection_fail", 0),
                           "heldout_solved": heldout_summary.get("solved_total", 0),
                           "heldout_unsolved": heldout_summary.get("unsolved_total", 0),
                           "heldout_fallback_only": heldout_summary.get("fallback_only", 0),
                           "heldout_adversarial_rejection_pass": heldout_summary.get("adversarial_rejection_pass", 0),
                           "heldout_adversarial_rejection_fail": heldout_summary.get("adversarial_rejection_fail", 0),
                           "exact_two_output_pass": payload.get("deterministic_replay_pass"),
                           "deterministic_replay_pass": payload.get("deterministic_replay_pass"),
                           "expected_output_isolation_pass": payload.get("expected_output_isolation_pass"),
                           "split_disjoint_pass": payload.get("split_disjoint_pass"),
                       })
        event_log.finish_run(summary)
        event_log.close()

        print(f"run_id: {run_id}")
        print(f"log_dir: {log_dir}")
        print(f"events.jsonl: {log_dir / 'events.jsonl'}")
        print(f"run.log: {log_dir / 'run.log'}")
        print(f"summary.json: {log_dir / 'summary.json'}")
        print(f"total_tasks: {heldout_summary.get('total_tasks', 0)}")
        print(f"solved: {heldout_summary.get('solved_total', 0)}")
        print(f"fallback_only: {heldout_summary.get('fallback_only', 0)}")
        print(f"exceptions: {heldout_summary.get('exception_count', 0)}")
        print(f"adversarial_rejection_pass: {heldout_summary.get('adversarial_rejection_pass', 0)}")
        print(f"adversarial_rejection_fail: {heldout_summary.get('adversarial_rejection_fail', 0)}")
        print(f"exact_two_output_pass: {payload.get('deterministic_replay_pass')}")
        print(f"deterministic_replay_pass: {payload.get('deterministic_replay_pass')}")
        print(f"expected_output_isolation_pass: {payload.get('expected_output_isolation_pass')}")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())