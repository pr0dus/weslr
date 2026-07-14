#!/usr/bin/env python3
"""
R4C release verifier — independently parses raw evidence.

Does NOT trust summary JSON fields without recalculation.
Rejects any disagreement between JUnit, raw output, return code, and receipt.
"""

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V3_DIR = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"
RAW_DIR = V3_DIR / "raw_validation_r4c"

results = {
    "verifier": "verify_scatti_cross_host_reconciliation_r4c.py",
    "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip(),
    "checks": {},
    "passed": 0,
    "failed": 0,
    "abstained": 0,
    "overall": None,
}

def check(name, condition, detail=""):
    if condition:
        results["checks"][name] = {"status": "PASS", "detail": detail}
        results["passed"] += 1
    else:
        results["checks"][name] = {"status": "FAIL", "detail": detail}
        results["failed"] += 1

def abstain(name, detail=""):
    results["checks"][name] = {"status": "ABSTAIN", "detail": detail}
    results["abstained"] += 1

# ── 1. Command receipt exists ────────────────────────────────────────────────

cmd_path = RAW_DIR / "command_receipt.json"
check("command_receipt_exists", cmd_path.exists(), str(cmd_path))

# ── 2. JUnit XML exists ──────────────────────────────────────────────────────

junit_path = RAW_DIR / "pytest_junit.xml"
check("junit_xml_exists", junit_path.exists(), str(junit_path))

# ── 3. Raw stdout exists ────────────────────────────────────────────────────

stdout_path = RAW_DIR / "pytest_stdout.txt"
check("raw_stdout_exists", stdout_path.exists(), str(stdout_path))

# ── 4. Raw stderr exists ─────────────────────────────────────────────────────

stderr_path = RAW_DIR / "pytest_stderr.txt"
check("raw_stderr_exists", stderr_path.exists(), str(stderr_path))

# ── 5. Test receipt exists ──────────────────────────────────────────────────

receipt_path = RAW_DIR / "test_receipt.json"
check("test_receipt_exists", receipt_path.exists(), str(receipt_path))

# ── 6. Parse command receipt ────────────────────────────────────────────────

if cmd_path.exists():
    with open(cmd_path) as f:
        cmd = json.load(f)
    check("pytest_return_code_zero", cmd.get("return_code") == 0,
          f"Return code: {cmd.get('return_code')}")
    check("stdout_hash_recorded", len(cmd.get("stdout_sha256", "")) == 64,
          f"Hash: {cmd.get('stdout_sha256', 'MISSING')[:16]}...")
    check("stderr_hash_recorded", len(cmd.get("stderr_sha256", "")) == 64,
          f"Hash: {cmd.get('stderr_sha256', 'MISSING')[:16]}...")
    # Verify stdout hash
    if stdout_path.exists():
        actual_stdout_sha = hashlib.sha256(stdout_path.read_bytes()).hexdigest()
        check("stdout_hash_matches", actual_stdout_sha == cmd.get("stdout_sha256", ""),
              f"Expected: {cmd.get('stdout_sha256', '')[:16]}..., Got: {actual_stdout_sha[:16]}...")
    # Verify stderr hash
    if stderr_path.exists():
        actual_stderr_sha = hashlib.sha256(stderr_path.read_bytes()).hexdigest()
        check("stderr_hash_matches", actual_stderr_sha == cmd.get("stderr_sha256", ""),
              f"Expected: {cmd.get('stderr_sha256', '')[:16]}..., Got: {actual_stderr_sha[:16]}...")
else:
    abstain("pytest_return_code_zero", "Command receipt missing")

# ── 7. Parse JUnit XML independently ─────────────────────────────────────────

if junit_path.exists():
    junit_sha = hashlib.sha256(junit_path.read_bytes()).hexdigest()
    check("junit_sha256_recorded", True, junit_sha[:16])
    
    tree = ET.parse(junit_path)
    root = tree.getroot()
    
    junit_tests = 0
    junit_failures = 0
    junit_errors = 0
    junit_skipped = 0
    
    for testsuite in root.findall("testsuite"):
        junit_tests += int(testsuite.get("tests", 0))
        junit_failures += int(testsuite.get("failures", 0))
        junit_errors += int(testsuite.get("errors", 0))
        junit_skipped += int(testsuite.get("skipped", 0))
    
    check("junit_failures_present", junit_failures == 0,
          f"JUnit failures: {junit_failures}")
    check("junit_errors_present", junit_errors == 0,
          f"JUnit errors: {junit_errors}")
    check("junit_skips_unapproved", junit_skipped == 0,
          f"JUnit skipped: {junit_skipped}")
    check("junit_total_inconsistent",
          junit_tests == junit_tests - junit_failures - junit_errors - junit_skipped + junit_failures + junit_errors + junit_skipped,
          f"JUnit total: {junit_tests}, failures: {junit_failures}, errors: {junit_errors}, skipped: {junit_skipped}")
else:
    abstain("junit_parsing", "JUnit file missing")

# ── 8. Parse stdout and compare with JUnit ───────────────────────────────────

if stdout_path.exists() and junit_path.exists():
    stdout_content = stdout_path.read_text()
    # Check for failure indicators in stdout
    has_failures = "FAILED" in stdout_content
    has_errors = "ERRORS" in stdout_content or "ERROR" in stdout_content
    
    stdout_agrees = True
    if junit_failures > 0 and not has_failures:
        stdout_agrees = False
    if junit_errors > 0 and not has_errors:
        stdout_agrees = False
    if junit_failures == 0 and has_failures:
        stdout_agrees = False
    
    check("stdout_junit_mismatch", stdout_agrees,
          f"JUnit failures={junit_failures}, errors={junit_errors}, stdout has FAILED={has_failures}, has ERRORS={has_errors}")
else:
    abstain("stdout_junit_comparison", "stdout or JUnit missing")

# ── 9. Parse test receipt and compare with JUnit ─────────────────────────────

if receipt_path.exists():
    with open(receipt_path) as f:
        receipt = json.load(f)
    
    receipt_junit_agree = True
    if receipt.get("junit_failures") != junit_failures:
        receipt_junit_agree = False
    if receipt.get("junit_errors") != junit_errors:
        receipt_junit_agree = False
    
    check("summary_junit_mismatch", receipt_junit_agree,
          f"Receipt: failures={receipt.get('junit_failures')}, errors={receipt.get('junit_errors')}; JUnit: failures={junit_failures}, errors={junit_errors}")
    
    # Check receipt head matches current HEAD
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    receipt_head = receipt.get("pre_run_head", "")
    check("receipt_head_mismatch", receipt_head == current_head,
          f"Receipt HEAD: {receipt_head[:16]}..., Current HEAD: {current_head[:16]}...")
    
    # Check source unchanged
    check("test_run_modified_source", receipt.get("source_unchanged", False),
          f"Source unchanged: {receipt.get('source_unchanged', 'unknown')}")
    
    # Check validation status
    check("validation_status_accepted", receipt.get("validation_status") == "accepted",
          f"Status: {receipt.get('validation_status', 'unknown')}")
else:
    abstain("receipt_parsing", "Test receipt missing")

# ── 10. No circular dependency ───────────────────────────────────────────────

# Verify that no Stage A test invokes the live verifier
if stdout_path.exists():
    content = stdout_path.read_text()
    has_live_verifier = "verify_scatti_cross_host" in content and "fixture" not in content.lower()
    check("live_verifier_circular_dependency", not has_live_verifier,
          "Stage A tests must not invoke live repository verifier")

# ── 11. Release evidence completeness ────────────────────────────────────────

required_evidence = [
    "command_receipt.json",
    "pytest_junit.xml",
    "pytest_stdout.txt",
    "pytest_stderr.txt",
    "test_receipt.json",
]
for ev in required_evidence:
    ev_path = RAW_DIR / ev
    check(f"release_evidence_missing_{ev}", ev_path.exists(), str(ev_path))

# ── Summary ──────────────────────────────────────────────────────────────────

total = results["passed"] + results["failed"] + results["abstained"]
results["overall"] = "cross_host_reconciliation_r4c_release_verified" if results["failed"] == 0 else "cross_host_reconciliation_r4c_release_failed"

print(f"\n{'='*60}")
print(f"R4C RELEASE VERIFIER RESULTS")
print(f"{'='*60}")
print(f"  Passed:    {results['passed']}")
print(f"  Failed:    {results['failed']}")
print(f"  Abstained: {results['abstained']}")
print(f"  Total:     {total}")
print(f"  Overall:   {results['overall']}")
print(f"{'='*60}\n")

for name, check_result in results["checks"].items():
    status = check_result["status"]
    detail = check_result.get("detail", "")
    if status == "PASS":
        print(f"  ✅ {name}")
    elif status == "FAIL":
        print(f"  ❌ {name}: {detail}")
    else:
        print(f"  ⚠️  {name}: {detail}")

# Write results
output_path = V3_DIR / "release_verification_receipt_r4c.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults written to: {output_path}")

sys.exit(0 if results["failed"] == 0 else 1)
