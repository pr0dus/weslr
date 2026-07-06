#!/usr/bin/env python3
"""WESLR ARC-AGI-2 Kaggle Format Submission Dry Run V1.

Runs the staged solver on public evaluation challenges and emits Kaggle-ready
submission JSON with no WESLR metadata.

This is not public scoring.
This is not a Kaggle submission.
This is not solver repair.

Usage:
    python scripts/run_kaggle_format_submission_dry_run_v1.py
    python scripts/run_kaggle_format_submission_dry_run_v1.py \\
        --challenges-json /path/to/challenges.json \\
        --output-json /path/to/output.json \\
        --work-dir /tmp/work
    python scripts/run_kaggle_format_submission_dry_run_v1.py --bare
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zipfile
import io
from copy import deepcopy

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

PUBLIC_ZIP_PATH = "/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip"
OUTPUT_DIR = "/data/data/com.termux/files/home/weslr-arc-public-eval-unscored-runs"
RUN_ID = "kaggle_format_v1"


def _load_challenges(path: str) -> dict:
    """Load challenges from a JSON file or zip member."""
    if path.endswith(".zip"):
        # Extract from zip
        member_name = os.path.basename(path).replace(".zip", ".json")
        with open(path, "rb") as f:
            z = zipfile.ZipFile(io.BytesIO(f.read()))
            return json.loads(z.read(member_name))
    with open(path) as f:
        return json.load(f)


def _run_solver_and_convert(
    challenges: dict,
    output_path: str,
    *,
    measure: bool = False,
) -> dict:
    """Run solver and convert to Kaggle format.

    Returns timing dict if measure=True.
    """
    from weslr_arc_solver.portable_solver import solve_challenges
    from weslr_arc_solver.kaggle_format import (
        convert_weslr_to_kaggle_v1,
        validate_kaggle_submission_v1,
    )

    timing = {}

    t0 = time.time()
    weslr_packet = solve_challenges(challenges)
    timing["solve"] = time.time() - t0

    t0 = time.time()
    kaggle_output = convert_weslr_to_kaggle_v1(weslr_packet)
    timing["convert"] = time.time() - t0

    t0 = time.time()
    with open(output_path, "w") as f:
        json.dump(kaggle_output, f, indent=2)
    timing["write"] = time.time() - t0

    t0 = time.time()
    validation = validate_kaggle_submission_v1(kaggle_output)
    timing["validate"] = time.time() - t0

    if measure:
        return {"output": kaggle_output, "validation": validation, "timing": timing}
    return {"output": kaggle_output, "validation": validation}


def _check_risky_patterns(staging_dir: str) -> dict:
    """Search for risky patterns in staged package."""
    import re

    patterns = {
        "/data/data/com.termux": r"/data/data/com\.termux",
        "arc-agi2-public-source": r"arc-agi2-public-source",
        "expected_output": r"expected_output",
        "solution": r"\bsolution\b",
        "public_solution": r"public_solution",
        "answer_key": r"answer_key",
        "kaggle_ready": r"kaggle_ready",
        "synthetic_only": r"synthetic_only",
        "schema_version": r"schema_version",
        "metadata": r"\bmetadata\b",
        "requests": r"\brequests\b",
        "http": r"\bhttp\b",
        "openai": r"\bopenai\b",
        "anthropic": r"\banthropic\b",
        "google": r"\bgoogle\b",
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


def main():
    parser = argparse.ArgumentParser(
        description="WESLR ARC-AGI-2 Kaggle Format Submission Dry Run V1"
    )
    parser.add_argument("--challenges-json", help="Path to challenges JSON file")
    parser.add_argument("--output-json", help="Path to write Kaggle-format output")
    parser.add_argument("--work-dir", help="Working directory")
    parser.add_argument("--bare", action="store_true",
                        help="Bare mode: minimal output, machine-readable log")
    args = parser.parse_args()

    # ── Resolve paths ──────────────────────────────────────────────────────
    if args.challenges_json:
        challenges_path = args.challenges_json
    else:
        challenges_path = PUBLIC_ZIP_PATH  # Will extract arc-agi_evaluation_challenges.json

    work_dir = args.work_dir or os.path.join(OUTPUT_DIR, RUN_ID)
    os.makedirs(work_dir, exist_ok=True)

    output_path = args.output_json or os.path.join(work_dir, "submission_kaggle_format.json")
    log_path = os.path.join(work_dir, "run_log.json")

    # ── Load challenges ─────────────────────────────────────────────────────
    t0 = time.time()
    if challenges_path == PUBLIC_ZIP_PATH:
        with open(PUBLIC_ZIP_PATH, "rb") as f:
            z = zipfile.ZipFile(io.BytesIO(f.read()))
            challenges = json.loads(z.read("arc-agi_evaluation_challenges.json"))
    else:
        with open(challenges_path) as f:
            challenges = json.loads(f)
    t_parse = time.time() - t0

    # ── Import ─────────────────────────────────────────────────────────────
    t0 = time.time()
    from weslr_arc_solver.portable_solver import solve_challenges
    from weslr_arc_solver.kaggle_format import (
        convert_weslr_to_kaggle_v1,
        validate_kaggle_submission_v1,
    )
    t_import = time.time() - t0

    # ── Solve ──────────────────────────────────────────────────────────────
    t0 = time.time()
    weslr_packet = solve_challenges(challenges)
    t_solve = time.time() - t0

    # ── Convert ────────────────────────────────────────────────────────────
    t0 = time.time()
    kaggle_output = convert_weslr_to_kaggle_v1(weslr_packet)
    t_convert = time.time() - t0

    # ── Write ──────────────────────────────────────────────────────────────
    t0 = time.time()
    with open(output_path, "w") as f:
        json.dump(kaggle_output, f, indent=2)
    t_write = time.time() - t0

    # ── Validate ───────────────────────────────────────────────────────────
    t0 = time.time()
    validation = validate_kaggle_submission_v1(kaggle_output)
    t_validate = time.time() - t0

    total_time = time.time() - (t0 - t_validate - t_write - t_convert - t_solve - t_import - t_parse)

    # ── Check output for metadata ──────────────────────────────────────────
    output_json_str = json.dumps(kaggle_output)
    metadata_patterns = {
        "kaggle_ready": "kaggle_ready" in output_json_str,
        "synthetic_only": "synthetic_only" in output_json_str,
        "contract_name": "contract_name" in output_json_str,
        "contract_version": "contract_version" in output_json_str,
        "denied_authority": "denied_authority" in output_json_str,
        "leakage_flags": "leakage_flags" in output_json_str,
        "metadata": "metadata" in output_json_str,
        "schema_version": "schema_version" in output_json_str,
        "source_candidate_id": "source_candidate_id" in output_json_str,
        "confidence_label": "confidence_label" in output_json_str,
        "evidence_labels": "evidence_labels" in output_json_str,
        "attempt_id": "attempt_id" in output_json_str,
    }
    metadata_clean = not any(metadata_patterns.values())

    # ── Check output for forbidden content ─────────────────────────────────
    forbidden_checks = {
        "/data/data/com.termux": "/data/data/com.termux" in output_json_str,
        "arc-agi2-public-source": "arc-agi2-public-source" in output_json_str,
        "expected_output": "expected_output" in output_json_str,
        "solution": '"solution"' in output_json_str,
        "public_solution": "public_solution" in output_json_str,
        "answer_key": '"answer_key"' in output_json_str or '"answer_key":' in output_json_str,
    }
    forbidden_clean = not any(forbidden_checks.values())

    # ── Build log ──────────────────────────────────────────────────────────
    log = {
        "run_id": RUN_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "challenges": {
            "source": "arc-agi_evaluation_challenges.json" if challenges_path == PUBLIC_ZIP_PATH else challenges_path,
            "task_count": len(challenges),
            "test_input_count": sum(len(t.get("test", [])) for t in challenges.values()),
        },
        "output": {
            "path": output_path,
            "task_count": validation["task_count"],
            "test_input_count": validation["test_input_count"],
            "valid": validation["valid"],
            "issues": validation["issues"],
            "metadata_clean": metadata_clean,
            "forbidden_clean": forbidden_clean,
        },
        "timing": {
            "import_s": round(t_import, 3),
            "parse_s": round(t_parse, 3),
            "solve_s": round(t_solve, 3),
            "convert_s": round(t_convert, 3),
            "write_s": round(t_write, 3),
            "validate_s": round(t_validate, 3),
            "total_s": round(total_time, 3),
        },
        "no_solution_read": True,
        "no_scoring": True,
        "no_kaggle_submission": True,
    }

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    # ── Output ─────────────────────────────────────────────────────────────
    if args.bare:
        # Bare mode: machine-readable summary only
        print(json.dumps(log))
        return 0 if validation["valid"] and metadata_clean and forbidden_clean else 1

    # Full mode: human-readable
    print("=" * 60)
    print("WESLR ARC-AGI-2 Kaggle Format Submission Dry Run V1")
    print("=" * 60)
    print()

    print(f"Challenges: {log['challenges']['task_count']} tasks, "
          f"{log['challenges']['test_input_count']} test inputs")
    print(f"Output: {output_path}")
    print(f"Log: {log_path}")
    print()

    print("Validation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Tasks: {validation['task_count']}")
    print(f"  Test inputs: {validation['test_input_count']}")
    if validation["issues"]:
        print(f"  Issues ({len(validation['issues'])}):")
        for issue in validation["issues"][:10]:
            print(f"    - {issue}")
    print()

    print("Metadata check:")
    for name, found in metadata_patterns.items():
        print(f"  {name}: {'FOUND' if found else 'clean'}")
    print()

    print("Forbidden content check:")
    for name, found in forbidden_checks.items():
        print(f"  {name}: {'FOUND' if found else 'clean'}")
    print()

    print("Timing:")
    for name, value in log["timing"].items():
        print(f"  {name}: {value}s")
    print()

    print("Boundary:")
    print(f"  No solution files read: {log['no_solution_read']}")
    print(f"  No scoring: {log['no_scoring']}")
    print(f"  No Kaggle submission: {log['no_kaggle_submission']}")
    print()

    all_pass = validation["valid"] and metadata_clean and forbidden_clean
    if all_pass:
        print("=" * 60)
        print("KAGGLE FORMAT DRY RUN PASSED")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("KAGGLE FORMAT DRY RUN FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
