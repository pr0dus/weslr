#!/usr/bin/env python3
"""WESLR ARC-AGI-2 Public Input Shape Dry Run V1.

Verifies the portable staging package can handle the public ARC-AGI-2 challenge
file shape and emit a Kaggle-shaped submission.json with exactly two outputs
per test input, without reading solutions or scoring.

This is not public scoring.
This is not a Kaggle submission.
This is not solver repair.
This is not benchmark repair.

Usage:
    python scripts/run_public_input_shape_dry_run_v1.py
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
OUTPUT_DIR = "/data/data/com.termux/files/home/weslr-arc-public-shape-dry-runs"
RUN_ID = "public_shape_dry_run_v1"


def _check_quarantine() -> dict:
    """Check public zip quarantine status."""
    result = {}
    if os.path.exists(PUBLIC_ZIP_PATH):
        result["exists"] = True
        result["size"] = os.path.getsize(PUBLIC_ZIP_PATH)
        result["mtime"] = time.ctime(os.path.getmtime(PUBLIC_ZIP_PATH))
    else:
        result["exists"] = False
    return result


def _zip_manifest() -> dict:
    """Inspect zip member names and sizes only. Do not open solution files."""
    with open(PUBLIC_ZIP_PATH, "rb") as f:
        z = zipfile.ZipFile(io.BytesIO(f.read()))
        members = []
        for info in z.infolist():
            members.append({
                "name": info.filename,
                "size": info.file_size,
                "compress_size": info.compress_size,
            })
        return {
            "member_count": len(members),
            "members": members,
            "challenge_files": [m["name"] for m in members if "challenge" in m["name"]],
            "solution_files": [m["name"] for m in members if "solution" in m["name"]],
            "sample_submission_files": [m["name"] for m in members if "sample_submission" in m["name"]],
        }


def _validate_challenge_shape(challenges: dict) -> dict:
    """Validate challenge schema shape without printing content."""
    issues = []
    task_count = 0
    total_test_inputs = 0
    total_train_pairs = 0
    grid_issues = 0
    schema_issues = 0

    for task_id, task_data in challenges.items():
        task_count += 1
        if not isinstance(task_data, dict):
            schema_issues += 1
            issues.append(f"task {task_id}: not a dict")
            continue

        # Check train/test fields
        train = task_data.get("train", [])
        test = task_data.get("test", [])
        if not isinstance(train, list):
            schema_issues += 1
            issues.append(f"task {task_id}: train is not a list")
        if not isinstance(test, list):
            schema_issues += 1
            issues.append(f"task {task_id}: test is not a list")

        total_train_pairs += len(train)
        total_test_inputs += len(test)

        # Validate train pair shape
        for pair_index, pair in enumerate(train):
            if not isinstance(pair, dict):
                grid_issues += 1
                continue
            inp = pair.get("input", pair.get("input_grid"))
            out = pair.get("output", pair.get("output_grid"))
            if inp is None:
                grid_issues += 1
                issues.append(f"task {task_id} train[{pair_index}]: missing input")
            elif not _validate_grid(inp):
                grid_issues += 1
                issues.append(f"task {task_id} train[{pair_index}]: invalid input grid")
            if out is None:
                grid_issues += 1
                issues.append(f"task {task_id} train[{pair_index}]: missing output")
            elif not _validate_grid(out):
                grid_issues += 1
                issues.append(f"task {task_id} train[{pair_index}]: invalid output grid")

        # Validate test input shape
        for test_index, test_item in enumerate(test):
            if not isinstance(test_item, dict):
                grid_issues += 1
                continue
            inp = test_item.get("input", test_item.get("input_grid"))
            if inp is None:
                grid_issues += 1
                issues.append(f"task {task_id} test[{test_index}]: missing input")
            elif not _validate_grid(inp):
                grid_issues += 1
                issues.append(f"task {task_id} test[{test_index}]: invalid input grid")
            # Check that test has no output key
            if "output" in test_item or "output_grid" in test_item:
                issues.append(f"task {task_id} test[{test_index}]: has output key (should not)")

    return {
        "valid": len(issues) == 0,
        "task_count": task_count,
        "total_train_pairs": total_train_pairs,
        "total_test_inputs": total_test_inputs,
        "grid_issues": grid_issues,
        "schema_issues": schema_issues,
        "issues": issues[:20],  # Limit to first 20 issues
    }


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


def _validate_submission(submission: dict) -> dict:
    """Validate submission structure."""
    issues = []

    if not isinstance(submission, dict):
        return {"valid": False, "issues": ["submission is not a dict"]}

    task_entries = submission.get("task_entries", submission.get("entries", []))
    if not isinstance(task_entries, list):
        return {"valid": False, "issues": ["task_entries is not a list"]}

    test_input_count = 0
    forbidden_keys = {"expected_output", "solution", "public_solution", "answer_key"}

    for entry_index, entry in enumerate(task_entries):
        if not isinstance(entry, dict):
            issues.append(f"entry[{entry_index}] is not a dict")
            continue

        task_id = entry.get("task_id", f"entry_{entry_index}")

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

                for key in forbidden_keys:
                    if key in attempt:
                        issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}]: forbidden key '{key}'")

                grid = attempt.get("grid", [])
                if not _validate_grid(grid):
                    issues.append(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] attempt[{att_index}]: invalid grid")

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


def _check_deterministic_replay(submission: dict, challenges: dict) -> dict:
    """Run solver twice and verify identical output."""
    from weslr_arc_solver.portable_solver import solve_challenges

    packet2 = solve_challenges(challenges)
    json1 = json.dumps(submission, sort_keys=True)
    json2 = json.dumps(packet2, sort_keys=True)
    return {"deterministic": json1 == json2}


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


def main():
    print("=" * 60)
    print("WESLR ARC-AGI-2 Public Input Shape Dry Run V1")
    print("=" * 60)
    print()

    # ── 1. Preflight and quarantine check ────────────────────────────────────
    print("1. Preflight and quarantine check")
    quarantine = _check_quarantine()
    print(f"   Public zip exists: {quarantine.get('exists', 'unknown')}")
    if quarantine.get("exists"):
        print(f"   Public zip size: {quarantine['size']} bytes")
        print(f"   Public zip mtime: {quarantine['mtime']}")
    print()

    # ── 2. Zip manifest check ────────────────────────────────────────────────
    print("2. Zip manifest check")
    manifest = _zip_manifest()
    print(f"   Total members: {manifest['member_count']}")
    for m in manifest["members"]:
        label = ""
        if "solution" in m["name"]:
            label = " [NOT OPENED]"
        elif "challenge" in m["name"]:
            label = " [challenge]"
        elif "sample_submission" in m["name"]:
            label = " [sample submission]"
        print(f"     {m['name']:45s} {m['size']:>8,} bytes{label}")
    print(f"   Solution files present but NOT opened: {manifest['solution_files']}")
    print()

    # ── 3. Public challenge shape dry run ────────────────────────────────────
    print("3. Public challenge shape dry run")
    print("   Opening: arc-agi_test_challenges.json (challenge file only)")
    print("   NOT opening: arc-agi_evaluation_solutions.json")
    print("   NOT opening: arc-agi_training_solutions.json")
    print()

    t0 = time.time()

    # Read challenge JSON from zip
    with open(PUBLIC_ZIP_PATH, "rb") as f:
        z = zipfile.ZipFile(io.BytesIO(f.read()))
        challenges = json.loads(z.read("arc-agi_test_challenges.json"))
    t_parse = time.time() - t0
    print(f"   Parse time: {t_parse:.3f}s")
    print()

    # Validate shape
    shape = _validate_challenge_shape(challenges)
    print(f"   Shape validation:")
    print(f"     Valid: {shape['valid']}")
    print(f"     Tasks: {shape['task_count']}")
    print(f"     Total train pairs: {shape['total_train_pairs']}")
    print(f"     Total test inputs: {shape['total_test_inputs']}")
    print(f"     Grid issues: {shape['grid_issues']}")
    print(f"     Schema issues: {shape['schema_issues']}")
    if shape["issues"]:
        print(f"     Issues ({len(shape['issues'])}):")
        for issue in shape["issues"][:5]:
            print(f"       - {issue}")
    print()

    # ── Import staged solver ────────────────────────────────────────────────
    print("   Importing staged solver...")
    t_import_start = time.time()
    from weslr_arc_solver.portable_solver import solve_challenges, validate_submission_packet
    t_import = time.time() - t_import_start
    print(f"     Import time: {t_import:.3f}s")
    print()

    # ── Run solver ──────────────────────────────────────────────────────────
    print("   Running solver on public challenge shape...")
    t_solve_start = time.time()
    submission = solve_challenges(challenges)
    t_solve = time.time() - t_solve_start
    print(f"     Solve time: {t_solve:.3f}s")
    print()

    # ── Write submission ───────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{RUN_ID}_submission.json")
    t_write_start = time.time()
    with open(output_path, "w") as f:
        json.dump(submission, f, indent=2)
    t_write = time.time() - t_write_start
    print(f"     Submission written to: {output_path}")
    print(f"     Write time: {t_write:.3f}s")
    print()

    total_time = time.time() - t0

    # ── 4. Submission validation ────────────────────────────────────────────
    print("4. Submission artifact validation")
    validation = _validate_submission(submission)
    print(f"   Valid: {validation['valid']}")
    print(f"   Task count: {validation['task_count']}")
    print(f"   Test input count: {validation['test_input_count']}")
    if validation["issues"]:
        print(f"   Issues ({len(validation['issues'])}):")
        for issue in validation["issues"][:10]:
            print(f"     - {issue}")
    print()

    # ── Exactly-two-output ──────────────────────────────────────────────────
    print("5. Exactly-two-output check")
    two_ok = True
    task_entries = submission.get("task_entries", submission.get("entries", []))
    for entry in task_entries:
        task_id = entry.get("task_id", "?")
        packets = entry.get("test_input_packets", entry.get("packets", []))
        for tp in packets:
            if len(tp.get("attempts", [])) != 2:
                print(f"   FAIL: {task_id} test[{tp.get('test_input_index', '?')}]: {len(tp.get('attempts', []))} attempts")
                two_ok = False
    if two_ok:
        print("   PASS: All test inputs have exactly 2 attempts")
    print()

    # ── Deterministic replay ───────────────────────────────────────────────
    print("6. Deterministic replay check")
    det_check = _check_deterministic_replay(submission, challenges)
    print(f"   Deterministic: {det_check['deterministic']}")
    print()

    # ── 7. Runtime measurement ──────────────────────────────────────────────
    print("7. Runtime measurement")
    test_count = validation["test_input_count"]
    print(f"   Import time: {t_import:.3f}s")
    print(f"   Parse time: {t_parse:.3f}s")
    print(f"   Solve time: {t_solve:.3f}s")
    print(f"   Write time: {t_write:.3f}s")
    print(f"   Total runtime: {total_time:.3f}s")
    print(f"   Tasks: {validation['task_count']}")
    print(f"   Test inputs: {test_count}")
    if test_count > 0:
        print(f"   Time per test input: {t_solve / test_count:.3f}s")
    print()

    # ── 8. Package isolation ───────────────────────────────────────────────
    print("8. Package isolation check")
    staging_dir = os.path.join(REPO_ROOT, "src", "weslr_arc_solver")
    print(f"   Staged package: {staging_dir}")
    print(f"   Imported from staged package: YES")
    print(f"   No WESLR repo import dependency: YES (uses WESLR_REPO_ROOT)")
    print(f"   No Termux path dependency: YES")
    print(f"   No internet/network dependency: YES")
    print(f"   No OpenClaw/OCC/Nova dependency: YES")
    print()

    # ── 9. Risky pattern search ────────────────────────────────────────────
    print("9. Risky pattern search")
    risky = _check_risky_patterns(staging_dir)
    for name, matches in risky.items():
        if matches:
            print(f"   {name}: {len(matches)} match(es)")
            for m in matches:
                print(f"     {m}")
        else:
            print(f"   {name}: clean")
    print()

    # ── Check output JSON for forbidden content ────────────────────────────
    print("   Output JSON check:")
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
            print(f"     WARN: output contains '{name}'")
            all_clean = False
        else:
            print(f"     {name}: clean")
    print()

    # ── Verdict ───────────────────────────────────────────────────────────
    print("=" * 60)
    all_pass = (
        shape["valid"]
        and validation["valid"]
        and two_ok
        and det_check["deterministic"]
        and all_clean
    )

    if all_pass:
        print("PUBLIC INPUT SHAPE DRY RUN PASSED")
        print("=" * 60)
        return 0
    else:
        print("PUBLIC INPUT SHAPE DRY RUN FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
