#!/usr/bin/env python3
"""WESLR Broad‑Hard‑80 Offline Evidence Verification Script.

Verifies an offline evidence bundle created by weslr_bh80_offline_evidence.py.

Usage:
    python scripts/weslr_bh80_verify_offline_evidence.py \\
        --evidence-dir /tmp/bh80_evidence
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys


REQUIRED_FILES = [
    "BH80_OFFLINE_EVIDENCE.json",
    "BH80_SOURCE_HASHES.json",
    "SHA256SUMS.txt",
    "README_VERIFY.txt",
]

REQUIRED_EVIDENCE_FIELDS = [
    "schema",
    "label",
    "timestamp_utc",
    "repo",
    "python_version",
    "platform",
    "network_guard",
    "generator",
    "source_hashes",
    "audit_verdict_reference",
    "owner_attestation",
]

REQUIRED_REPO_FIELDS = ["root", "branch", "head", "head_short", "is_clean"]


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Verify WESLR BH80 Offline Evidence")
    parser.add_argument("--evidence-dir", required=True, help="Folder containing evidence bundle")
    parser.add_argument("--expected-head", default=None, help="Expected HEAD to verify")
    args = parser.parse_args()

    evidence_dir = os.path.abspath(args.evidence_dir)
    if not os.path.isdir(evidence_dir):
        print(f"FAIL: evidence dir does not exist: {evidence_dir}", file=sys.stderr)
        sys.exit(1)

    errors = []
    passes = []

    # 1. Required files exist
    for fname in REQUIRED_FILES:
        fpath = os.path.join(evidence_dir, fname)
        if not os.path.isfile(fpath):
            errors.append(f"Missing required file: {fname}")
        else:
            passes.append(f"File exists: {fname}")

    # 2. SHA256SUMS verification
    sha_path = os.path.join(evidence_dir, "SHA256SUMS.txt")
    if os.path.isfile(sha_path):
        with open(sha_path) as f:
            sha_lines = [line.strip() for line in f if line.strip()]
        for line in sha_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2:
                errors.append(f"Malformed SHA256SUMS line: {line}")
                continue
            expected_sha, fname = parts
            fpath = os.path.join(evidence_dir, fname)
            if not os.path.isfile(fpath):
                errors.append(f"SHA256SUMS references missing file: {fname}")
                continue
            actual_sha = _sha256_file(fpath)
            if actual_sha != expected_sha:
                errors.append(f"SHA256 mismatch for {fname}: expected {expected_sha}, got {actual_sha}")
            else:
                passes.append(f"SHA256 verified: {fname}")

    # 3. Evidence JSON schema
    evidence_path = os.path.join(evidence_dir, "BH80_OFFLINE_EVIDENCE.json")
    if os.path.isfile(evidence_path):
        with open(evidence_path) as f:
            evidence = json.load(f)

        for field in REQUIRED_EVIDENCE_FIELDS:
            if field not in evidence:
                errors.append(f"Evidence missing field: {field}")
            else:
                passes.append(f"Evidence field present: {field}")

        # Check repo subfields
        if "repo" in evidence:
            for field in REQUIRED_REPO_FIELDS:
                if field not in evidence["repo"]:
                    errors.append(f"Evidence repo missing field: {field}")
                else:
                    passes.append(f"Evidence repo field present: {field}")

        # Check generator
        gen = evidence.get("generator", {})
        if not gen.get("exists"):
            errors.append("Generator does not exist or import failed")
        elif gen.get("task_count") != 80:
            errors.append(f"Task count is {gen.get('task_count')}, expected 80")
        else:
            passes.append("Generator exists with 80 tasks")

        # Check network guard
        ng = evidence.get("network_guard", {})
        if not ng.get("enabled"):
            errors.append("Network guard was not enabled")
        else:
            passes.append("Network guard was enabled")

        # Check owner attestation
        attestation = evidence.get("owner_attestation", "")
        if "owner-attested" not in attestation:
            errors.append("Owner attestation statement missing or incorrect")
        else:
            passes.append("Owner attestation present")

        # Check audit verdict
        verdict = evidence.get("audit_verdict_reference", "")
        if not verdict:
            errors.append("Audit verdict reference missing")
        else:
            passes.append(f"Audit verdict: {verdict}")

        # Verify HEAD if expected
        if args.expected_head:
            head = evidence.get("repo", {}).get("head", "")
            head_short = evidence.get("repo", {}).get("head_short", "")
            if head.startswith(args.expected_head) or head_short == args.expected_head:
                passes.append(f"HEAD matches expected: {args.expected_head}")
            else:
                errors.append(f"HEAD mismatch: expected {args.expected_head}, got {head_short}")

    # 4. Source hashes verification (if run from same repo)
    src_hash_path = os.path.join(evidence_dir, "BH80_SOURCE_HASHES.json")
    if os.path.isfile(src_hash_path) and os.path.isfile(evidence_path):
        with open(src_hash_path) as f:
            stored_hashes = json.load(f)
        with open(evidence_path) as f:
            evidence = json.load(f)
        repo_root = evidence.get("repo", {}).get("root", "")
        if repo_root and os.path.isdir(repo_root):
            for rel, stored_sha in stored_hashes.items():
                if stored_sha == "FILE_NOT_FOUND":
                    passes.append(f"Source file was not found at evidence time: {rel}")
                    continue
                full = os.path.join(repo_root, rel)
                if not os.path.isfile(full):
                    errors.append(f"Source file missing now: {rel}")
                    continue
                current_sha = _sha256_file(full)
                if current_sha != stored_sha:
                    errors.append(f"Source hash mismatch for {rel}: evidence={stored_sha[:12]}, current={current_sha[:12]}")
                else:
                    passes.append(f"Source hash verified: {rel}")
        else:
            passes.append("Source hash verification skipped (repo root not accessible)")

    # Summary
    print("=" * 60)
    print("WESLR BH80 Offline Evidence Verification")
    print("=" * 60)
    print(f"\nEvidence dir: {evidence_dir}")
    print(f"Checks passed: {len(passes)}")
    print(f"Checks failed: {len(errors)}")
    print()

    if passes:
        print("--- PASSED ---")
        for p in passes:
            print(f"  ✅ {p}")
        print()

    if errors:
        print("--- FAILED ---")
        for e in errors:
            print(f"  ❌ {e}")
        print()
        print("VERDICT: FAIL")
        sys.exit(1)
    else:
        print("VERDICT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()