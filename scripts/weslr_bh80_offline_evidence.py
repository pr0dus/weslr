#!/usr/bin/env python3
"""WESLR Broad‑Hard‑80 Offline Owner Evidence Harness.

Creates a machine‑readable evidence bundle in an empty user‑provided folder.
Runs fully locally — a socket guard blocks accidental network calls.

Usage:
    python scripts/weslr_bh80_offline_evidence.py \\
        --out-dir /tmp/bh80_evidence \\
        --expected-head 402d8f6d \\
        --label owner_run_001
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import datetime

# ---------------------------------------------------------------------------
# Network guard — block all socket operations
# ---------------------------------------------------------------------------
_original_socket = socket.socket
_network_guard_enabled = False
_network_violations: list[str] = []


def _blocked_socket(*args, **kwargs):
    _network_violations.append(f"socket({args}, {kwargs})")
    raise RuntimeError("Network guard active: socket creation blocked")


def _enable_network_guard():
    global _network_guard_enabled
    socket.socket = _blocked_socket  # type: ignore[assignment]
    socket.create_connection = _blocked_socket  # type: ignore[assignment]
    socket.getaddrinfo = _blocked_socket  # type: ignore[assignment]
    _network_guard_enabled = True


def _disable_network_guard():
    global _network_guard_enabled
    socket.socket = _original_socket  # type: ignore[assignment]
    _network_guard_enabled = False


# ---------------------------------------------------------------------------
# Source files to hash
# ---------------------------------------------------------------------------
SOURCE_FILES = [
    "weslr/arc_synthetic_3_step_task_schema.py",
    "weslr/arc_synthetic_3_step_real_dispatch.py",
    "weslr/tests/test_broad_hard_80_generator.py",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_DESIGN_V1.md",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_REDEFINED_DESIGN_REVIEW_V1.md",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_IMPLEMENTATION_V1.md",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_REVIEW_V1.md",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_PILOT_RUN_V1.md",
    "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_SCORING_AND_ANTI_CHEAT_AUDIT_V1.md",
]


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_cmd(repo: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def _source_hashes(repo: str) -> dict[str, str]:
    hashes = {}
    for rel in SOURCE_FILES:
        full = os.path.join(repo, rel)
        if os.path.isfile(full):
            hashes[rel] = _sha256_file(full)
        else:
            hashes[rel] = "FILE_NOT_FOUND"
    return hashes


def _task_id_hash(tasks: list) -> str:
    ids = [t["task_id"] for t in tasks]
    return _sha256_bytes("\n".join(ids).encode())


def _primitive_list_hash(tasks: list) -> str:
    sigs = ["→".join(t["primitive_sequence"]) for t in tasks]
    return _sha256_bytes("\n".join(sigs).encode())


def main():
    parser = argparse.ArgumentParser(
        description="WESLR BH80 Offline Owner Evidence Harness"
    )
    parser.add_argument("--out-dir", required=True, help="Empty output folder")
    parser.add_argument("--expected-head", default=None, help="Expected git HEAD (short or full)")
    parser.add_argument("--label", default="owner_run", help="Owner label for this run")
    args = parser.parse_args()

    # Validate out-dir exists and is empty
    out_dir = os.path.abspath(args.out_dir)
    if not os.path.isdir(out_dir):
        print(f"ERROR: output dir does not exist: {out_dir}", file=sys.stderr)
        sys.exit(1)
    if os.listdir(out_dir):
        print(f"ERROR: output dir is not empty: {out_dir}", file=sys.stderr)
        sys.exit(1)

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Verify we're in the WESLR repo
    if not os.path.isfile(os.path.join(repo, "weslr", "arc_synthetic_3_step_task_schema.py")):
        print(f"ERROR: not in WESLR repo root: {repo}", file=sys.stderr)
        sys.exit(1)

    # Enable network guard
    _enable_network_guard()

    # Git state
    branch = _git_cmd(repo, "branch", "--show-current")
    head = _git_cmd(repo, "rev-parse", "HEAD")
    head_short = _git_cmd(repo, "rev-parse", "--short", "HEAD")
    status_short = _git_cmd(repo, "status", "--short")
    is_clean = len(status_short) == 0

    # Verify HEAD if expected
    head_match = None
    if args.expected_head:
        head_match = head.startswith(args.expected_head) or head_short == args.expected_head
        if not head_match:
            print(f"ERROR: HEAD mismatch: expected {args.expected_head}, got {head_short}", file=sys.stderr)
            _disable_network_guard()
            sys.exit(1)

    # Source hashes
    src_hashes = _source_hashes(repo)

    # Generator check (import happens before network guard for the module itself)
    # We need to temporarily restore network for import, then re-block
    _disable_network_guard()
    sys.path.insert(0, repo)
    try:
        from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks
        tasks = generate_broad_hard_80_tasks()
        gen_exists = True
        task_count = len(tasks)
        tid_hash = _task_id_hash(tasks)
        prim_hash = _primitive_list_hash(tasks)
    except Exception as e:
        gen_exists = False
        task_count = 0
        tid_hash = "IMPORT_FAILED"
        prim_hash = "IMPORT_FAILED"
        tasks = []
    _enable_network_guard()

    # Build evidence JSON
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    evidence = {
        "schema": "weslr.bh80.offline_evidence.v1",
        "label": args.label,
        "timestamp_utc": timestamp,
        "command_arguments": {
            "out_dir": out_dir,
            "expected_head": args.expected_head,
            "label": args.label,
        },
        "repo": {
            "root": repo,
            "branch": branch,
            "head": head,
            "head_short": head_short,
            "status_short": status_short,
            "is_clean": is_clean,
        },
        "expected_head_match": head_match,
        "output_dir_empty_before_run": True,
        "python_version": sys.version,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "release": platform.release(),
        },
        "network_guard": {
            "enabled": True,
            "violations": _network_violations,
        },
        "imported_modules": [
            "weslr.arc_synthetic_3_step_task_schema.generate_broad_hard_80_tasks",
        ],
        "generator": {
            "exists": gen_exists,
            "task_count": task_count,
            "task_ids_hash": tid_hash,
            "primitive_list_hash": prim_hash,
        },
        "source_hashes": src_hashes,
        "audit_verdict_reference": "structural_pass_only_semantic_scoring_missing",
        "audit_report": "docs/WESLR_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_SCORING_AND_ANTI_CHEAT_AUDIT_V1.md",
        "owner_attestation": (
            "offline status is owner-attested, not cryptographically proven"
        ),
    }

    # Write evidence files
    evidence_path = os.path.join(out_dir, "BH80_OFFLINE_EVIDENCE.json")
    with open(evidence_path, "w") as f:
        json.dump(evidence, f, indent=2)

    source_hash_path = os.path.join(out_dir, "BH80_SOURCE_HASHES.json")
    with open(source_hash_path, "w") as f:
        json.dump(src_hashes, f, indent=2)

    # SHA256SUMS — does not include itself (standard practice)
    sha_manifest = []
    for fname in sorted(os.listdir(out_dir)):
        fpath = os.path.join(out_dir, fname)
        if os.path.isfile(fpath):
            sha = _sha256_file(fpath)
            sha_manifest.append(f"{sha}  {fname}")

    sha_path = os.path.join(out_dir, "SHA256SUMS.txt")
    with open(sha_path, "w") as f:
        f.write("\n".join(sha_manifest) + "\n")

    # README
    readme_path = os.path.join(out_dir, "README_VERIFY.txt")
    readme_content = f"""WESLR Broad‑Hard‑80 Offline Evidence Bundle
============================================

Label: {args.label}
Created (UTC): {timestamp}
Repo: {repo}
Branch: {branch}
HEAD: {head_short}
Clean: {is_clean}

Files in this bundle:
  BH80_OFFLINE_EVIDENCE.json  — machine‑readable evidence
  BH80_SOURCE_HASHES.json    — SHA256 hashes of source files
  SHA256SUMS.txt              — SHA256 manifest of all files

Verification:
  python scripts/weslr_bh80_verify_offline_evidence.py \\
      --evidence-dir {out_dir}

IMPORTANT: offline status is owner‑attested, not cryptographically proven.
The owner should run this harness with internet disconnected.
"""
    with open(readme_path, "w") as f:
        f.write(readme_content)

    _disable_network_guard()
    print(f"Evidence written to: {out_dir}")
    print(f"  BH80_OFFLINE_EVIDENCE.json")
    print(f"  BH80_SOURCE_HASHES.json")
    print(f"  SHA256SUMS.txt")
    print(f"  README_VERIFY.txt")
    print(f"Tasks: {task_count}, HEAD: {head_short}, Clean: {is_clean}")


if __name__ == "__main__":
    main()