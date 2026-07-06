#!/usr/bin/env python3
"""WESLR ARC-AGI-2 Portable Submission Package Smoke Test V1.

Runs a Kaggle-style offline dry run of the portable submission package using
only tiny synthetic/sample challenge data created locally.

This is not public scoring.
This is not a Kaggle submission.
This must not read public ARC task contents.
This must not use public solutions.
This must not repair solver capability.

Usage:
    python scripts/run_portable_submission_package_smoke_v1.py
    python scripts/run_portable_submission_package_smoke_v1.py \\
        --challenges-path /tmp/challenges.json \\
        --output-path /tmp/submission.json \\
        --work-dir /tmp/work
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from copy import deepcopy

# Add repo root to path for importing the staging package
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))


def _make_synthetic_challenge() -> dict:
    """Create a tiny synthetic challenge with:
    - at least two task IDs
    - at least one task with multiple test inputs
    - at least one task solvable by a known family
    - at least one task requiring fallback/top-2 behavior
    - no expected outputs in solver-visible input
    """
    # Task 1: Simple color-role task (copy input grid as-is)
    # This is solvable by the color_role family
    task1 = {
        "train": [
            {
                "input": [[1, 0], [0, 1]],
                "output": [[1, 0], [0, 1]],
            },
            {
                "input": [[2, 0], [0, 2]],
                "output": [[2, 0], [0, 2]],
            },
        ],
        "test": [
            {"input": [[3, 0], [0, 3]]},
            {"input": [[4, 0], [0, 4]]},
        ],
    }

    # Task 2: Object bbox task (crop to non-zero region)
    # Solvable by object_bbox family
    task2 = {
        "train": [
            {
                "input": [[0, 0, 0], [0, 5, 0], [0, 0, 0]],
                "output": [[5]],
            },
            {
                "input": [[0, 0, 0, 0], [0, 6, 6, 0], [0, 6, 6, 0], [0, 0, 0, 0]],
                "output": [[6, 6], [6, 6]],
            },
        ],
        "test": [
            {"input": [[0, 0, 0, 0], [0, 7, 7, 0], [0, 7, 7, 0], [0, 0, 0, 0]]},
        ],
    }

    # Task 3: Fallback task (no clear family match)
    # This should trigger fallback behavior
    task3 = {
        "train": [
            {
                "input": [[1, 2], [3, 4]],
                "output": [[4, 3], [2, 1]],
            },
        ],
        "test": [
            {"input": [[5, 6], [7, 8]]},
            {"input": [[9, 1], [2, 3]]},
        ],
    }

    return {
        "smoke_test_color_role": task1,
        "smoke_test_object_bbox": task2,
        "smoke_test_fallback": task3,
    }


def _make_expected_outputs() -> dict:
    """Create expected outputs for scoring the synthetic challenge.

    These are NOT passed to the solver — only used for post-hoc scoring.
    """
    return {
        "smoke_test_color_role": [
            [[3, 0], [0, 3]],
            [[4, 0], [0, 4]],
        ],
        "smoke_test_object_bbox": [
            [[7, 7], [7, 7]],
        ],
        "smoke_test_fallback": [
            [[8, 7], [6, 5]],
            [[3, 2], [1, 9]],
        ],
    }


def _validate_submission(submission: dict) -> dict:
    """Validate submission structure."""
    issues = []

    if not isinstance(submission, dict):
        return {"valid": False, "issues": ["submission is not a dict"]}

    task_entries = submission.get("task_entries", submission.get("entries", []))
    if not isinstance(task_entries, list):
        return {"valid": False, "issues": ["task_entries is not a list"]}

    if not task_entries:
        return {"valid": False, "issues": ["no task entries"]}

    test_input_count = 0
    forbidden_keys = {"expected_output", "solution", "public_solution"}

    for entry_index, entry in enumerate(task_entries):
        if not isinstance(entry, dict):
            issues.append(f"entry[{entry_index}] is not a dict")
            continue

        task_id = entry.get("task_id", f"entry_{entry_index}")

        # Check forbidden keys
        for key in forbidden_keys:
            if key in entry:
                issues.append(f"entry[{entry_index}] ({task_id}): forbidden key '{key}'")

        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        if not isinstance(test_packets, list):
            issues.append(f"entry[{entry_index}] ({task_id}): test_input_packets is not a list")
            continue

        for pkt_index, tp in enumerate(test_packets):
            if not isinstance(tp, dict):
                issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: not a dict")
                continue

            test_input_count += 1

            # Check forbidden keys
            for key in forbidden_keys:
                if key in tp:
                    issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: forbidden key '{key}'")

            attempts = tp.get("attempts", [])
            if not isinstance(attempts, list):
                issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: attempts is not a list")
                continue

            if len(attempts) != 2:
                issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: expected 2 attempts, got {len(attempts)}")

            for att_index, attempt in enumerate(attempts):
                if not isinstance(attempt, dict):
                    issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}]: not a dict")
                    continue

                # Check forbidden keys
                for key in forbidden_keys:
                    if key in attempt:
                        issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}]: forbidden key '{key}'")

                grid = attempt.get("grid", [])
                if not isinstance(grid, list) or not grid:
                    issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}]: invalid grid")
                    continue

                for row_index, row in enumerate(grid):
                    if not isinstance(row, list):
                        issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}] grid[{row_index}]: not a list")
                        continue
                    for col_index, cell in enumerate(row):
                        if not isinstance(cell, int) or cell < 0 or cell > 9:
                            issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}] grid[{row_index}][{col_index}]: invalid cell {cell}")

    # Check for absolute local paths
    packet_json = json.dumps(submission)
    if "/data/data/com.termux" in packet_json:
        issues.append("submission JSON contains /data/data/com.termux path")
    if "arc-agi2-public-source" in packet_json:
        issues.append("submission JSON contains arc-agi2-public-source path")

    return {
        "valid": len(issues) == 0,
        "task_count": len(task_entries),
        "test_input_count": test_input_count,
        "issues": issues,
    }


def _check_exactly_two_attempts(submission: dict) -> dict:
    """Verify exactly 2 attempts per test input."""
    issues = []
    task_entries = submission.get("task_entries", submission.get("entries", []))
    for entry in task_entries:
        task_id = entry.get("task_id", "unknown")
        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        for pkt_index, tp in enumerate(test_packets):
            attempts = tp.get("attempts", [])
            if len(attempts) != 2:
                issues.append(f"{task_id} test[{pkt_index}]: {len(attempts)} attempts (expected 2)")
            for att_index, attempt in enumerate(attempts):
                rank = attempt.get("rank", att_index + 1)
                if rank != att_index + 1:
                    issues.append(f"{task_id} test[{pkt_index}] attempt[{att_index}]: rank={rank}, expected {att_index + 1}")
    return {"valid": len(issues) == 0, "issues": issues}


def _check_deterministic_replay(submission: dict, challenges: dict) -> dict:
    """Run solver twice and verify identical output."""
    from weslr_arc_solver.portable_solver import solve_challenges

    packet2 = solve_challenges(challenges)
    json1 = json.dumps(submission, sort_keys=True)
    json2 = json.dumps(packet2, sort_keys=True)
    return {"deterministic": json1 == json2}


def _check_no_network(staging_dir: str) -> dict:
    """Search staged package for network-related patterns."""
    import re

    patterns = {
        "requests": r"\brequests\b",
        "http": r"\bhttp\b",
        "openai": r"\bopenai\b",
        "anthropic": r"\banthropic\b",
        "google": r"\bgoogle\b",
        "socket": r"\bsocket\b",
        "urllib": r"\burllib\b",
    }

    results = {}
    for name, pattern in patterns.items():
        matches = []
        for root, dirs, files in os.walk(staging_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        for line_no, line in enumerate(fh, 1):
                            if re.search(pattern, line):
                                rel_path = os.path.relpath(path, staging_dir)
                                matches.append(f"{rel_path}:{line_no}: {line.strip()[:80]}")
        results[name] = matches

    return results


def _check_risky_patterns(staging_dir: str) -> dict:
    """Search for risky patterns in staged package."""
    import re

    patterns = {
        "/data/data/com.termux": r"/data/data/com\.termux",
        "arc-agi2-public-source": r"arc-agi2-public-source",
        "expected_output": r"expected_output",
        "solution": r"\bsolution\b",
        "public_solution": r"public_solution",
        "subprocess": r"\bsubprocess\b",
    }

    results = {}
    for name, pattern in patterns.items():
        matches = []
        for root, dirs, files in os.walk(staging_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        for line_no, line in enumerate(fh, 1):
                            if re.search(pattern, line):
                                rel_path = os.path.relpath(path, staging_dir)
                                matches.append(f"{rel_path}:{line_no}: {line.strip()[:80]}")
        results[name] = matches

    return results


def _check_public_data_boundary() -> dict:
    """Check public data boundary."""
    public_zip = "/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip"
    results = {}
    if os.path.exists(public_zip):
        import stat
        st = os.stat(public_zip)
        results["public_zip_exists"] = True
        results["public_zip_size"] = st.st_size
        results["public_zip_mtime"] = time.ctime(st.st_mtime)
    else:
        results["public_zip_exists"] = False
    return results


def _list_staged_modules(staging_dir: str) -> list:
    """List bundled modules in the staging package."""
    modules = []
    for f in sorted(os.listdir(staging_dir)):
        if f.endswith(".py") and f != "__init__.py":
            modules.append(f.replace(".py", ""))
    return modules


def main():
    parser = argparse.ArgumentParser(
        description="WESLR ARC-AGI-2 Portable Submission Package Smoke Test V1"
    )
    parser.add_argument("--challenges-path", help="Path to write synthetic challenges JSON")
    parser.add_argument("--output-path", help="Path to write submission JSON")
    parser.add_argument("--work-dir", help="Working directory for temp files")
    args = parser.parse_args()

    print("=" * 60)
    print("WESLR ARC-AGI-2 Portable Submission Package Smoke Test V1")
    print("=" * 60)
    print()

    # ── Setup ────────────────────────────────────────────────────────────────
    work_dir = args.work_dir or tempfile.mkdtemp(prefix="weslr_smoke_")
    challenges_path = args.challenges_path or os.path.join(work_dir, "challenges.json")
    output_path = args.output_path or os.path.join(work_dir, "submission.json")

    os.makedirs(work_dir, exist_ok=True)

    # ── Build synthetic challenge ────────────────────────────────────────────
    print("Building synthetic challenge...")
    challenges = _make_synthetic_challenge()
    with open(challenges_path, "w") as f:
        json.dump(challenges, f, indent=2)
    print(f"  Tasks: {len(challenges)}")
    print(f"  Task IDs: {list(challenges.keys())}")
    for tid, tdata in challenges.items():
        print(f"    {tid}: {len(tdata['train'])} train, {len(tdata['test'])} test")
    print()

    # ── Import solver ────────────────────────────────────────────────────────
    print("Importing portable solver...")
    t0 = time.time()
    from weslr_arc_solver.portable_solver import solve_challenges, validate_submission_packet
    t_import = time.time() - t0
    print(f"  Import time: {t_import:.3f}s")
    print()

    # ── Run solver ──────────────────────────────────────────────────────────
    print("Running solver on synthetic challenge...")
    t0 = time.time()
    submission = solve_challenges(challenges)
    t_solve = time.time() - t0
    print(f"  Solve time: {t_solve:.3f}s")
    print(f"  Output written to: {output_path}")
    with open(output_path, "w") as f:
        json.dump(submission, f, indent=2)
    print()

    # ── Validate submission ──────────────────────────────────────────────────
    print("Validating submission packet...")
    validation = _validate_submission(submission)
    print(f"  Valid: {validation['valid']}")
    print(f"  Task count: {validation['task_count']}")
    print(f"  Test input count: {validation['test_input_count']}")
    if validation["issues"]:
        print(f"  Issues ({len(validation['issues'])}):")
        for issue in validation["issues"]:
            print(f"    - {issue}")
    print()

    # ── Exactly-two-output validation ────────────────────────────────────────
    print("Checking exactly-two-output...")
    two_output = _check_exactly_two_attempts(submission)
    print(f"  Valid: {two_output['valid']}")
    if two_output["issues"]:
        for issue in two_output["issues"]:
            print(f"    - {issue}")
    print()

    # ── Deterministic replay ─────────────────────────────────────────────────
    print("Checking deterministic replay...")
    det_check = _check_deterministic_replay(submission, challenges)
    print(f"  Deterministic: {det_check['deterministic']}")
    print()

    # ── No-network check ──────────────────────────────────────────────────────
    staging_dir = os.path.join(REPO_ROOT, "src", "weslr_arc_solver")
    print("Checking no-network patterns...")
    net_check = _check_no_network(staging_dir)
    all_clean = True
    for name, matches in net_check.items():
        if matches:
            all_clean = False
            print(f"  {name}: {len(matches)} match(es)")
            for m in matches:
                print(f"    {m}")
        else:
            print(f"  {name}: clean")
    print()

    # ── Risky pattern search ─────────────────────────────────────────────────
    print("Checking risky patterns...")
    risky = _check_risky_patterns(staging_dir)
    for name, matches in risky.items():
        if matches:
            print(f"  {name}: {len(matches)} match(es)")
            for m in matches:
                print(f"    {m}")
        else:
            print(f"  {name}: clean")
    print()

    # ── Public data boundary ─────────────────────────────────────────────────
    print("Checking public data boundary...")
    pub_check = _check_public_data_boundary()
    print(f"  Public zip exists: {pub_check.get('public_zip_exists', 'unknown')}")
    if pub_check.get("public_zip_exists"):
        print(f"  Public zip size: {pub_check.get('public_zip_size', 'unknown')} bytes")
        print(f"  Public zip mtime: {pub_check.get('public_zip_mtime', 'unknown')}")
    print()

    # ── Staged modules ────────────────────────────────────────────────────────
    print("Staged package modules:")
    modules = _list_staged_modules(staging_dir)
    for mod in modules:
        print(f"  - {mod}")
    print()

    # ── Runtime summary ────────────────────────────────────────────────────────
    total_time = t_import + t_solve
    test_count = validation["test_input_count"]
    print(f"Runtime summary:")
    print(f"  Import time: {t_import:.3f}s")
    print(f"  Solve time: {t_solve:.3f}s")
    print(f"  Total runtime: {total_time:.3f}s")
    print(f"  Tasks: {validation['task_count']}")
    print(f"  Test inputs: {test_count}")
    if test_count > 0:
        print(f"  Time per test input: {t_solve / test_count:.3f}s")
    print()

    # ── Submission summary ───────────────────────────────────────────────────
    print("Submission summary:")
    task_entries = submission.get("task_entries", submission.get("entries", []))
    for entry in task_entries:
        task_id = entry.get("task_id", "unknown")
        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        for pkt_index, tp in enumerate(test_packets):
            attempts = tp.get("attempts", [])
            for att in attempts:
                grid = att.get("grid", [])
                rank = att.get("rank", "?")
                family = att.get("source_candidate_id", "?")
                h, w = len(grid), len(grid[0]) if grid else 0
                print(f"  {task_id} test[{pkt_index}]: rank={rank} family={family} grid={h}x{w}")
    print()

    # ── Verdict ───────────────────────────────────────────────────────────────
    all_pass = (
        validation["valid"]
        and two_output["valid"]
        and det_check["deterministic"]
        and all_clean
    )

    if all_pass:
        print("=" * 60)
        print("SMOKE TEST PASSED")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("SMOKE TEST FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
