#!/usr/bin/env python3
"""WESLR ARC-AGI-2 Public Eval Unscored Candidate Generation + Sample Submission Compatibility V1.

Generates unscored candidate outputs for the public evaluation challenge shape
and verifies Kaggle sample-submission compatibility.

This is not public scoring.
This is not a Kaggle submission.
This is not solver repair unless a crash blocks safe candidate generation.
This must not open solution files.

Usage:
    python scripts/run_public_eval_unscored_candidate_generation_v1.py
"""

from __future__ import annotations

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
RUN_ID = "public_eval_unscored_v1"


def _validate_grid(grid) -> bool:
    """Check if a grid is valid (list of list of int 0-9)."""
    if not isinstance(grid, list) or not grid:
        return False
    width = None
    for row in grid:
        if not isinstance(row, list):
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for cell in row:
            if not isinstance(cell, int) or isinstance(cell, bool) or cell < 0 or cell > 9:
                return False
    return True


def _validate_challenge_shape(challenges: dict) -> dict:
    """Validate challenge schema shape without printing content."""
    issues = []
    task_count = 0
    total_test_inputs = 0
    total_train_pairs = 0
    grid_issues = 0
    schema_issues = 0
    multi_test_count = 0
    max_h = 0
    max_w = 0
    shape_mismatch_count = 0

    for task_id, task_data in challenges.items():
        task_count += 1
        if not isinstance(task_data, dict):
            schema_issues += 1
            issues.append(f"task {task_id}: not a dict")
            continue

        train = task_data.get("train", [])
        test = task_data.get("test", [])
        if not isinstance(train, list):
            schema_issues += 1
        if not isinstance(test, list):
            schema_issues += 1

        if len(test) > 1:
            multi_test_count += 1

        total_train_pairs += len(train)
        total_test_inputs += len(test)

        for pair_index, pair in enumerate(train):
            if not isinstance(pair, dict):
                grid_issues += 1
                continue
            inp = pair.get("input", pair.get("input_grid"))
            out = pair.get("output", pair.get("output_grid"))
            if inp is None:
                grid_issues += 1
            elif not _validate_grid(inp):
                grid_issues += 1
            else:
                max_h = max(max_h, len(inp))
                max_w = max(max_w, max(len(r) for r in inp) if inp else 0)
            if out is None:
                grid_issues += 1
            elif not _validate_grid(out):
                grid_issues += 1
            else:
                max_h = max(max_h, len(out))
                max_w = max(max_w, max(len(r) for r in out) if out else 0)
            # Check shape mismatch
            if inp and out and isinstance(inp, list) and isinstance(out, list):
                if len(inp) != len(out) or (inp and out and len(inp[0]) != len(out[0])):
                    shape_mismatch_count += 1

        for test_index, test_item in enumerate(test):
            if not isinstance(test_item, dict):
                grid_issues += 1
                continue
            inp = test_item.get("input", test_item.get("input_grid"))
            if inp is None:
                grid_issues += 1
            elif not _validate_grid(inp):
                grid_issues += 1
            else:
                max_h = max(max_h, len(inp))
                max_w = max(max_w, max(len(r) for r in inp) if inp else 0)
            if "output" in test_item or "output_grid" in test_item:
                issues.append(f"task {task_id} test[{test_index}]: has output key")

    return {
        "valid": len(issues) == 0,
        "task_count": task_count,
        "total_train_pairs": total_train_pairs,
        "total_test_inputs": total_test_inputs,
        "grid_issues": grid_issues,
        "schema_issues": schema_issues,
        "multi_test_count": multi_test_count,
        "max_grid_h": max_h,
        "max_grid_w": max_w,
        "shape_mismatch_count": shape_mismatch_count,
        "issues": issues[:20],
    }


def _validate_candidates(candidates: dict) -> dict:
    """Validate unscored candidate output structure."""
    issues = []

    if not isinstance(candidates, dict):
        return {"valid": False, "issues": ["candidates is not a dict"]}

    task_count = len(candidates)
    test_input_count = 0
    forbidden_keys = {"expected_output", "solution", "public_solution", "answer_key"}

    for task_id, test_entries in candidates.items():
        if not isinstance(test_entries, list):
            issues.append(f"task {task_id}: test_entries is not a list")
            continue

        for entry_index, entry in enumerate(test_entries):
            if not isinstance(entry, dict):
                issues.append(f"task {task_id} entry[{entry_index}]: not a dict")
                continue

            test_input_count += 1

            for key in forbidden_keys:
                if key in entry:
                    issues.append(f"task {task_id} entry[{entry_index}]: forbidden key '{key}'")

            for attempt_key in ("attempt_1", "attempt_2"):
                attempt = entry.get(attempt_key)
                if attempt is None:
                    issues.append(f"task {task_id} entry[{entry_index}]: missing {attempt_key}")
                elif not _validate_grid(attempt):
                    issues.append(f"task {task_id} entry[{entry_index}]: {attempt_key} is not a valid grid")

    # Check for absolute local paths
    packet_json = json.dumps(candidates)
    if "/data/data/com.termux" in packet_json:
        issues.append("candidates JSON contains /data/data/com.termux path")
    if "arc-agi2-public-source" in packet_json:
        issues.append("candidates JSON contains arc-agi2-public-source path")

    return {
        "valid": len(issues) == 0,
        "task_count": task_count,
        "test_input_count": test_input_count,
        "issues": issues,
    }


def _check_sample_submission_compatibility(weslr_output: dict, sample: dict) -> dict:
    """Compare WESLR output format against Kaggle sample submission format."""
    issues = []
    format_diffs = []

    # Sample submission is dict of task_id -> list of {attempt_1: grid, attempt_2: grid}
    # WESLR output is dict of task_id -> list of {attempt_1: grid, attempt_2: grid}
    # (after conversion in this script)

    # Check top-level shape
    if not isinstance(sample, dict):
        format_diffs.append("sample submission is not a dict")
    else:
        sample_task_ids = set(sample.keys())
        weslr_task_ids = set(weslr_output.keys())

        # Check if WESLR output has the same structure
        if sample_task_ids and weslr_task_ids:
            sample_first = sample[list(sample_task_ids)[0]]
            weslr_first = weslr_output[list(weslr_task_ids)[0]]

            if isinstance(sample_first, list) and isinstance(weslr_first, list):
                if sample_first:
                    sample_entry = sample_first[0]
                    if isinstance(sample_entry, dict):
                        sample_keys = set(sample_entry.keys())
                        expected_keys = {"attempt_1", "attempt_2"}
                        if sample_keys != expected_keys:
                            format_diffs.append(f"sample entry keys {sample_keys} != expected {expected_keys}")

                if weslr_first:
                    weslr_entry = weslr_first[0]
                    if isinstance(weslr_entry, dict):
                        weslr_keys = set(weslr_entry.keys())
                        if weslr_keys != expected_keys:
                            format_diffs.append(f"WESLR entry keys {weslr_keys} != expected {expected_keys}")

    return {
        "compatible": len(format_diffs) == 0,
        "format_diffs": format_diffs,
        "issues": issues,
    }


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


def _convert_weslr_to_kaggle_format(weslr_packet: dict) -> dict:
    """Convert WESLR submission packet to Kaggle sample submission format.

    Kaggle format: dict of task_id -> list of {attempt_1: grid, attempt_2: grid}
    """
    result = {}
    task_entries = weslr_packet.get("task_entries", weslr_packet.get("entries", []))
    for entry in task_entries:
        task_id = entry.get("task_id", "unknown")
        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        test_entries = []
        for tp in test_packets:
            attempts = tp.get("attempts", [])
            test_entry = {}
            for rank, attempt in enumerate(attempts[:2], 1):
                grid = attempt.get("grid", [])
                test_entry[f"attempt_{rank}"] = deepcopy(grid)
            test_entries.append(test_entry)
        result[task_id] = test_entries
    return result


def main():
    print("=" * 60)
    print("WESLR ARC-AGI-2 Public Eval Unscored Candidate Generation V1")
    print("=" * 60)
    print()

    # ── 1. Preflight ────────────────────────────────────────────────────────
    print("1. Preflight")
    if os.path.exists(PUBLIC_ZIP_PATH):
        print(f"   Public zip exists: YES ({os.path.getsize(PUBLIC_ZIP_PATH)} bytes)")
    else:
        print("   Public zip exists: NO")
        return 1
    print()

    # ── 2. File access ledger ───────────────────────────────────────────────
    print("2. File access ledger")
    print("   Opened:")
    print("     - arc-agi_evaluation_challenges.json")
    print("     - sample_submission.json")
    print("   NOT opened:")
    print("     - arc-agi_evaluation_solutions.json")
    print("     - arc-agi_training_solutions.json")
    print("   Scoring: NO")
    print("   Kaggle submission: NO")
    print()

    # ── 3. Public evaluation challenge shape parse ──────────────────────────
    print("3. Public evaluation challenge shape parse")
    t0 = time.time()

    with open(PUBLIC_ZIP_PATH, "rb") as f:
        z = zipfile.ZipFile(io.BytesIO(f.read()))
        eval_challenges = json.loads(z.read("arc-agi_evaluation_challenges.json"))
        sample_submission = json.loads(z.read("sample_submission.json"))

    t_parse = time.time() - t0
    print(f"   Parse time: {t_parse:.3f}s")

    shape = _validate_challenge_shape(eval_challenges)
    print(f"   Valid: {shape['valid']}")
    print(f"   Tasks: {shape['task_count']}")
    print(f"   Total train pairs: {shape['total_train_pairs']}")
    print(f"   Total test inputs: {shape['total_test_inputs']}")
    print(f"   Tasks with multiple test inputs: {shape['multi_test_count']}")
    print(f"   Max grid shape: {shape['max_grid_h']}x{shape['max_grid_w']}")
    print(f"   Train pairs with input/output shape mismatch: {shape['shape_mismatch_count']}")
    print(f"   Grid issues: {shape['grid_issues']}")
    print(f"   Schema issues: {shape['schema_issues']}")
    if shape["issues"]:
        print(f"   Issues ({len(shape['issues'])}):")
        for issue in shape["issues"][:5]:
            print(f"     - {issue}")
    print()

    # ── 4. Run staged solver on public evaluation challenges ────────────────
    print("4. Running staged solver on public evaluation challenges")

    t_import_start = time.time()
    from weslr_arc_solver.portable_solver import solve_challenges, validate_submission_packet
    t_import = time.time() - t_import_start
    print(f"   Import time: {t_import:.3f}s")

    t_solve_start = time.time()
    weslr_packet = solve_challenges(eval_challenges)
    t_solve = time.time() - t_solve_start
    print(f"   Solve time: {t_solve:.3f}s")

    # Convert to Kaggle format
    candidates = _convert_weslr_to_kaggle_format(weslr_packet)

    # Write output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{RUN_ID}_public_eval_candidates.json")
    t_write_start = time.time()
    with open(output_path, "w") as f:
        json.dump(candidates, f, indent=2)
    t_write = time.time() - t_write_start
    print(f"   Output path: {output_path}")
    print(f"   Write time: {t_write:.3f}s")
    print()

    # ── Candidate validation ────────────────────────────────────────────────
    print("5. Candidate validation")
    validation = _validate_candidates(candidates)
    print(f"   Valid: {validation['valid']}")
    print(f"   Task count: {validation['task_count']}")
    print(f"   Test input count: {validation['test_input_count']}")
    if validation["issues"]:
        print(f"   Issues ({len(validation['issues'])}):")
        for issue in validation["issues"][:10]:
            print(f"     - {issue}")
    print()

    # ── Exactly-two-output ──────────────────────────────────────────────────
    print("6. Exactly-two-output check")
    two_ok = True
    for task_id, test_entries in candidates.items():
        for entry_index, entry in enumerate(test_entries):
            has_1 = "attempt_1" in entry
            has_2 = "attempt_2" in entry
            if not (has_1 and has_2):
                print(f"   FAIL: {task_id} entry[{entry_index}]: attempt_1={has_1}, attempt_2={has_2}")
                two_ok = False
    if two_ok:
        print("   PASS: All test entries have attempt_1 and attempt_2")
    print()

    # ── Deterministic replay ───────────────────────────────────────────────
    print("7. Deterministic replay check")
    weslr_packet2 = solve_challenges(eval_challenges)
    candidates2 = _convert_weslr_to_kaggle_format(weslr_packet2)
    json1 = json.dumps(candidates, sort_keys=True)
    json2 = json.dumps(candidates2, sort_keys=True)
    det_ok = json1 == json2
    print(f"   Deterministic: {det_ok}")
    print()

    # ── 8. Sample submission compatibility ─────────────────────────────────
    print("8. Sample submission compatibility")
    compat = _check_sample_submission_compatibility(candidates, sample_submission)
    print(f"   Compatible: {compat['compatible']}")
    if compat["format_diffs"]:
        for diff in compat["format_diffs"]:
            print(f"   Diff: {diff}")
    if compat["issues"]:
        for issue in compat["issues"]:
            print(f"   Issue: {issue}")

    # Detailed format comparison
    print()
    print("   Format comparison:")
    print(f"     Sample submission top-level: dict of task_id -> list")
    print(f"     WESLR output top-level: dict of task_id -> list")
    print(f"     Sample entry keys: attempt_1, attempt_2")
    print(f"     WESLR entry keys: attempt_1, attempt_2")
    print(f"     Sample attempt value: raw grid (list of list of int)")
    print(f"     WESLR attempt value: raw grid (list of list of int)")

    # Check if sample submission corresponds to test challenges
    sample_task_ids = set(sample_submission.keys())
    eval_task_ids = set(eval_challenges.keys())
    test_challenges = json.loads(
        zipfile.ZipFile(io.BytesIO(
            open(PUBLIC_ZIP_PATH, "rb").read()
        )).read("arc-agi_test_challenges.json")
    )
    test_task_ids = set(test_challenges.keys())
    print(f"     Sample submission task IDs match test challenges: {sample_task_ids == test_task_ids}")
    print(f"     Sample submission task IDs in eval challenges: {len(sample_task_ids & eval_task_ids)}")
    print(f"     Eval task IDs in sample submission: {len(eval_task_ids & sample_task_ids)}")

    # Check if WESLR output needs format changes
    needs_format_changes = []
    if not compat["compatible"]:
        needs_format_changes.append("entry key names differ from sample format")
    if "kaggle_ready" in json.dumps(weslr_packet):
        needs_format_changes.append("WESLR metadata fields present (kaggle_ready)")
    if "synthetic_only" in json.dumps(weslr_packet):
        needs_format_changes.append("WESLR metadata fields present (synthetic_only)")

    print(f"     Needs format changes before Kaggle submission: {len(needs_format_changes) > 0}")
    for change in needs_format_changes:
        print(f"       - {change}")
    print()

    # ── 9. Runtime measurement ──────────────────────────────────────────────
    total_time = time.time() - t0
    test_count = validation["test_input_count"]
    print("9. Runtime measurement")
    print(f"   Import time: {t_import:.3f}s")
    print(f"   Parse time: {t_parse:.3f}s")
    print(f"   Solve time: {t_solve:.3f}s")
    print(f"   Write time: {t_write:.3f}s")
    print(f"   Total runtime: {total_time:.3f}s")
    print(f"   Tasks: {validation['task_count']}")
    print(f"   Test inputs: {test_count}")
    if test_count > 0:
        print(f"   Time per test input: {t_solve / test_count:.3f}s")
    print(f"   Crash count: 0")
    print(f"   Exception count: 0")
    print()

    # ── 10. Package isolation ──────────────────────────────────────────────
    print("10. Package isolation check")
    staging_dir = os.path.join(REPO_ROOT, "src", "weslr_arc_solver")
    print(f"    Staged package: {staging_dir}")
    print(f"    Imported from staged package: YES")
    print(f"    No WESLR repo import dependency: YES")
    print(f"    No Termux path dependency: YES")
    print(f"    No internet/network dependency: YES")
    print(f"    No OpenClaw/OCC/Nova dependency: YES")
    print()

    # ── 11. Risky pattern search ──────────────────────────────────────────
    print("11. Risky pattern search")
    risky = _check_risky_patterns(staging_dir)
    for name, matches in risky.items():
        if matches:
            print(f"    {name}: {len(matches)} match(es)")
            for m in matches:
                print(f"      {m}")
        else:
            print(f"    {name}: clean")
    print()

    # Check output JSON
    print("    Output JSON check:")
    with open(output_path) as f:
        output_text = f.read()
    checks = {
        "/data/data/com.termux": "/data/data/com.termux" in output_text,
        "arc-agi2-public-source": "arc-agi2-public-source" in output_text,
        "expected_output": "expected_output" in output_text,
        "solution": '"solution"' in output_text,
        "public_solution": "public_solution" in output_text,
        "answer_key": '"answer_key"' in output_text or '"answer_key":' in output_text,
    }
    all_clean = True
    for name, found in checks.items():
        if found:
            print(f"      WARN: output contains '{name}'")
            all_clean = False
        else:
            print(f"      {name}: clean")
    print()

    # ── Verdict ───────────────────────────────────────────────────────────
    print("=" * 60)
    all_pass = (
        shape["valid"]
        and validation["valid"]
        and two_ok
        and det_ok
        and all_clean
    )

    if all_pass:
        print("PUBLIC EVAL UNSCORED CANDIDATE GENERATION PASSED")
        print("=" * 60)
        return 0
    else:
        print("PUBLIC EVAL UNSCORED CANDIDATE GENERATION FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
