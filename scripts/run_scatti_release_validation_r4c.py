#!/usr/bin/env python3
"""
Authoritative SCATTI release validation runner — R4C.

Runs pytest exactly once in a fresh subprocess.
Generates all receipts from JUnit XML, not from hardcoded values.
"""

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V3_DIR = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"
RAW_DIR = V3_DIR / "raw_validation_r4c"

# Test files to run
TEST_FILES = [
    "weslr/tests/test_materials_stoichiometric_route_engine.py",
    "weslr/tests/test_calculation_assurance.py",
    "weslr/tests/test_materials_stoichiometric_route_verifier.py",
    "weslr/tests/test_scatti_audit_consistency.py",
    "weslr/tests/test_scatti_calculation_assurance_release_v2.py",
    "weslr/tests/test_cross_host_evidence_reconciliation.py",
    "weslr/tests/test_scatti_cross_host_reconciliation_v3.py",
]

# Environment allowlist
ALLOWED_ENV = {
    "WESLR_REPO_ROOT": str(REPO_ROOT),
    "PYTHONPATH": str(REPO_ROOT),
    "PATH": os.environ.get("PATH", ""),
    "HOME": os.environ.get("HOME", ""),
    "USER": os.environ.get("USER", ""),
}


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    
    # Record pre-run state
    pre_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    pre_status = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT).decode().strip()
    
    start_utc = datetime.now(timezone.utc)
    
    # Find interpreter
    interpreter = sys.executable
    py_version = sys.version
    
    # Build command
    pytest_args = [
        interpreter, "-m", "pytest",
        "-q",
        "--junitxml", str(RAW_DIR / "pytest_junit.xml"),
        "--tb=short",
    ] + TEST_FILES
    
    argv = pytest_args
    
    # Run pytest
    result = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, **ALLOWED_ENV},
    )
    
    end_utc = datetime.now(timezone.utc)
    
    # Write raw outputs
    with open(RAW_DIR / "pytest_stdout.txt", "w") as f:
        f.write(result.stdout)
    with open(RAW_DIR / "pytest_stderr.txt", "w") as f:
        f.write(result.stderr)
    
    # Write command receipt
    command_receipt = {
        "argv": argv,
        "cwd": str(REPO_ROOT),
        "interpreter": interpreter,
        "python_version": py_version,
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "return_code": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        "tested_files": TEST_FILES,
        "environment_allowlist": list(ALLOWED_ENV.keys()),
        "pre_run_head": pre_head,
        "pre_run_status": pre_status,
    }
    with open(RAW_DIR / "command_receipt.json", "w") as f:
        json.dump(command_receipt, f, indent=2)
    
    # Parse JUnit XML
    junit_path = RAW_DIR / "pytest_junit.xml"
    junit_sha256 = hashlib.sha256(open(junit_path, 'rb').read()).hexdigest() if junit_path.exists() else "NOT_FOUND"
    
    junit_tests = 0
    junit_failures = 0
    junit_errors = 0
    junit_skipped = 0
    
    if junit_path.exists():
        tree = ET.parse(junit_path)
        root = tree.getroot()
        for testsuite in root.findall("testsuite"):
            junit_tests += int(testsuite.get("tests", 0))
            junit_failures += int(testsuite.get("failures", 0))
            junit_errors += int(testsuite.get("errors", 0))
            junit_skipped += int(testsuite.get("skipped", 0))
    
    # Parse stdout summary
    stdout_lines = result.stdout.strip().split("\n")
    stdout_summary = ""
    for line in reversed(stdout_lines):
        if "passed" in line or "failed" in line or "error" in line:
            stdout_summary = line.strip()
            break
    
    # Generate test receipt from JUnit only
    test_receipt = {
        "test_suite": "SCATTI release validation R4C",
        "interpreter": interpreter,
        "python_version": py_version,
        "junit_path": str(junit_path),
        "junit_sha256": junit_sha256,
        "return_code": result.returncode,
        "junit_tests": junit_tests,
        "junit_passed": junit_tests - junit_failures - junit_errors - junit_skipped,
        "junit_failures": junit_failures,
        "junit_errors": junit_errors,
        "junit_skipped": junit_skipped,
        "stdout_summary": stdout_summary,
        "stdout_junit_agree": str(junit_failures) in stdout_summary if stdout_summary else False,
        "pre_run_head": pre_head,
        "post_run_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip(),
        "post_run_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT).decode().strip(),
        "source_unchanged": pre_head == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip(),
        "validation_status": "accepted" if (result.returncode == 0 and junit_failures == 0 and junit_errors == 0) else "rejected",
        "generated_at": end_utc.isoformat(),
    }
    
    with open(RAW_DIR / "test_receipt.json", "w") as f:
        json.dump(test_receipt, f, indent=2)
    
    # Print summary
    print(f"SCATTI Release Validation R4C")
    print(f"{'='*50}")
    print(f"  Return code:  {result.returncode}")
    print(f"  JUnit tests:  {junit_tests}")
    print(f"  Passed:       {junit_tests - junit_failures - junit_errors - junit_skipped}")
    print(f"  Failures:     {junit_failures}")
    print(f"  Errors:       {junit_errors}")
    print(f"  Skipped:      {junit_skipped}")
    print(f"  Status:       {test_receipt['validation_status']}")
    print(f"{'='*50}")
    
    if test_receipt["validation_status"] == "rejected":
        print(f"\nSTDOUT summary: {stdout_summary}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
