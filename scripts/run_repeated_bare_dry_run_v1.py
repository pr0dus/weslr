#!/usr/bin/env python3
"""Run repeated bare-mode Kaggle-format dry runs and collect results.

Usage:
    python scripts/run_repeated_bare_dry_run_v1.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_BASE = "/data/data/com.termux/files/home/weslr-arc-public-eval-unscored-runs/repeated_bare_v1"
NUM_RUNS = 5

SCRIPT = os.path.join(REPO_ROOT, "scripts", "run_kaggle_format_submission_dry_run_v1.py")


def main():
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    results = []

    for run_index in range(1, NUM_RUNS + 1):
        run_dir = os.path.join(OUTPUT_BASE, f"run_{run_index:02d}")
        os.makedirs(run_dir, exist_ok=True)

        output_path = os.path.join(run_dir, "submission_kaggle_format.json")
        log_path = os.path.join(run_dir, "run_log.json")

        start_time = time.time()
        start_str = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        proc = subprocess.run(
            [sys.executable, SCRIPT, "--bare",
             "--output-json", output_path,
             "--work-dir", run_dir],
            capture_output=True, text=True, timeout=600,
        )

        end_time = time.time()
        end_str = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        elapsed = round(end_time - start_time, 3)
        exit_code = proc.returncode

        # Parse bare output
        run_data = {}
        if proc.stdout.strip():
            try:
                run_data = json.loads(proc.stdout.strip())
            except json.JSONDecodeError:
                run_data = {"parse_error": proc.stdout.strip()[:200]}

        # Compute output SHA256
        output_sha256 = None
        output_size = None
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                output_sha256 = hashlib.sha256(f.read()).hexdigest()
            output_size = os.path.getsize(output_path)

        result = {
            "run_index": run_index,
            "start_time": start_str,
            "end_time": end_str,
            "elapsed_s": elapsed,
            "exit_code": exit_code,
            "output_path": output_path,
            "output_size_bytes": output_size,
            "output_sha256": output_sha256,
            "log_path": log_path,
            "run_data": run_data,
        }
        results.append(result)

        print(f"Run {run_index:02d}: exit={exit_code} elapsed={elapsed}s "
              f"output={output_size} bytes sha256={output_sha256[:16] if output_sha256 else 'N/A'}...")

    # ── Summary ────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("REPEATED BARE DRY RUN SUMMARY")
    print("=" * 60)
    print()

    # Exit codes
    all_exit_zero = all(r["exit_code"] == 0 for r in results)
    print(f"All runs exit 0: {all_exit_zero}")

    # Output hashes
    hashes = [r["output_sha256"] for r in results if r["output_sha256"]]
    all_hashes_match = len(set(hashes)) == 1 if hashes else False
    print(f"All output hashes match: {all_hashes_match}")
    if hashes:
        print(f"  Hash: {hashes[0]}")

    # Output sizes
    sizes = [r["output_size_bytes"] for r in results if r["output_size_bytes"] is not None]
    if sizes:
        print(f"Output sizes: min={min(sizes)} max={max(sizes)} "
              f"mean={sum(sizes)//len(sizes)}")

    # Timing
    timings = [r["elapsed_s"] for r in results]
    if timings:
        print(f"Timing (total): min={min(timings):.3f}s max={max(timings):.3f}s "
              f"mean={sum(timings)/len(timings):.3f}s "
              f"median={sorted(timings)[len(timings)//2]:.3f}s")

    # Per-phase timing
    solve_times = [r["run_data"].get("timing", {}).get("solve_s", 0) for r in results if "run_data" in r]
    if solve_times:
        print(f"Solve time: min={min(solve_times):.3f}s max={max(solve_times):.3f}s "
              f"mean={sum(solve_times)/len(solve_times):.3f}s")

    # Validation
    all_valid = all(
        r["run_data"].get("output", {}).get("valid", False)
        for r in results if "run_data" in r
    )
    print(f"All outputs valid: {all_valid}")

    all_metadata_clean = all(
        r["run_data"].get("output", {}).get("metadata_clean", False)
        for r in results if "run_data" in r
    )
    print(f"All metadata clean: {all_metadata_clean}")

    all_forbidden_clean = all(
        r["run_data"].get("output", {}).get("forbidden_clean", False)
        for r in results if "run_data" in r
    )
    print(f"All forbidden clean: {all_forbidden_clean}")

    # Task/test counts
    task_counts = [r["run_data"].get("output", {}).get("task_count", 0) for r in results if "run_data" in r]
    test_counts = [r["run_data"].get("output", {}).get("test_input_count", 0) for r in results if "run_data" in r]
    if task_counts:
        print(f"Task count: {task_counts[0]} (all runs)")
    if test_counts:
        print(f"Test input count: {test_counts[0]} (all runs)")

    # Boundary
    no_solution = all(
        r["run_data"].get("no_solution_read", False)
        for r in results if "run_data" in r
    )
    no_scoring = all(
        r["run_data"].get("no_scoring", False)
        for r in results if "run_data" in r
    )
    no_kaggle = all(
        r["run_data"].get("no_kaggle_submission", False)
        for r in results if "run_data" in r
    )
    print(f"No solution read: {no_solution}")
    print(f"No scoring: {no_scoring}")
    print(f"No Kaggle submission: {no_kaggle}")

    # Write summary
    summary = {
        "num_runs": NUM_RUNS,
        "all_exit_zero": all_exit_zero,
        "all_output_hashes_match": all_hashes_match,
        "canonical_output_hash": hashes[0] if hashes else None,
        "output_sizes": sizes,
        "timing_total_s": timings,
        "timing_solve_s": solve_times,
        "all_outputs_valid": all_valid,
        "all_metadata_clean": all_metadata_clean,
        "all_forbidden_clean": all_forbidden_clean,
        "task_count": task_counts[0] if task_counts else None,
        "test_input_count": test_counts[0] if test_counts else None,
        "no_solution_read": no_solution,
        "no_scoring": no_scoring,
        "no_kaggle_submission": no_kaggle,
        "runs": results,
    }

    summary_path = os.path.join(OUTPUT_BASE, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSummary written to: {summary_path}")

    return 0 if (all_exit_zero and all_hashes_match and all_valid
                 and all_metadata_clean and all_forbidden_clean) else 1


if __name__ == "__main__":
    sys.exit(main())
