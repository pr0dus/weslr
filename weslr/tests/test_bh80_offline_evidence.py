"""Tests for the BH80 offline evidence harness and verification script."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVIDENCE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "weslr_bh80_offline_evidence.py")
VERIFY_SCRIPT = os.path.join(REPO_ROOT, "scripts", "weslr_bh80_verify_offline_evidence.py")


@pytest.fixture
def evidence_dir():
    d = tempfile.mkdtemp(prefix="bh80_evidence_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def evidence_dir_nonempty(tmp_path):
    d = tmp_path / "nonempty"
    d.mkdir()
    (d / "somefile.txt").write_text("content")
    return str(d)


class TestOfflineEvidenceHarness:
    def test_refuses_nonempty_dir(self, evidence_dir_nonempty):
        result = subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir_nonempty, "--label", "test"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert "not empty" in result.stderr

    def test_creates_evidence_files(self, evidence_dir):
        result = subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir, "--label", "test_run"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        for fname in ["BH80_OFFLINE_EVIDENCE.json", "BH80_SOURCE_HASHES.json", "SHA256SUMS.txt", "README_VERIFY.txt"]:
            assert os.path.isfile(os.path.join(evidence_dir, fname)), f"Missing: {fname}"

    def test_evidence_json_has_required_fields(self, evidence_dir):
        subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir, "--label", "test"],
            capture_output=True, text=True, timeout=30,
        )
        with open(os.path.join(evidence_dir, "BH80_OFFLINE_EVIDENCE.json")) as f:
            ev = json.load(f)
        for field in ["schema", "label", "timestamp_utc", "repo", "python_version", "platform",
                       "network_guard", "generator", "source_hashes", "audit_verdict_reference",
                       "owner_attestation"]:
            assert field in ev, f"Missing field: {field}"
        assert ev["schema"] == "weslr.bh80.offline_evidence.v1"
        assert ev["generator"]["task_count"] == 80
        assert ev["network_guard"]["enabled"] is True
        assert "owner-attested" in ev["owner_attestation"]

    def test_head_mismatch_fails(self, evidence_dir):
        result = subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir,
             "--expected-head", "0000000", "--label", "test"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert "HEAD mismatch" in result.stderr


class TestVerificationScript:
    def test_verifies_valid_evidence(self, evidence_dir):
        # Create evidence
        subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir, "--label", "verify_test"],
            capture_output=True, text=True, timeout=30,
        )
        # Verify
        result = subprocess.run(
            [sys.executable, VERIFY_SCRIPT, "--evidence-dir", evidence_dir],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VERDICT: PASS" in result.stdout

    def test_fails_on_missing_file(self, evidence_dir):
        subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir, "--label", "test"],
            capture_output=True, text=True, timeout=30,
        )
        # Remove a file
        os.remove(os.path.join(evidence_dir, "README_VERIFY.txt"))
        result = subprocess.run(
            [sys.executable, VERIFY_SCRIPT, "--evidence-dir", evidence_dir],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert "VERDICT: FAIL" in result.stdout

    def test_verifies_expected_head(self, evidence_dir):
        # Get current HEAD
        head_result = subprocess.run(
            ["git", "-C", REPO_ROOT, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        head = head_result.stdout.strip()
        subprocess.run(
            [sys.executable, EVIDENCE_SCRIPT, "--out-dir", evidence_dir,
             "--expected-head", head, "--label", "head_test"],
            capture_output=True, text=True, timeout=30,
        )
        result = subprocess.run(
            [sys.executable, VERIFY_SCRIPT, "--evidence-dir", evidence_dir,
             "--expected-head", head],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout
        assert "HEAD matches expected" in result.stdout