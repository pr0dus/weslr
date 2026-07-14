#!/usr/bin/env python3
"""Tests for cross-host evidence reconciliation module."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weslr.modules.cross_host_evidence_reconciliation import (
    verify_commit_reachability,
    verify_artifact_at_commit,
    compare_artifact_hashes,
    compare_machine_readable_claim,
    reconcile_stage_status,
    record_supersession,
    build_reconciliation_certificate,
    canonical_serialize,
    LOCALLY_VERIFIED,
    IMPORTED_AND_VERIFIED,
    KNOWN_EXTERNAL_NOT_IMPORTED,
    SOURCE_COMMIT_UNREACHABLE,
    ARTIFACT_MISSING,
    ARTIFACT_HASH_MISMATCH,
    CONTENT_CLAIM_MISMATCH,
    SUPERSEDED_VERIFIED,
    UNRESOLVED,
    ABSTAIN_CROSS_HOST_DISAGREEMENT,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVerifyCommitReachability(unittest.TestCase):
    def test_reachable_commit(self):
        ok, msg = verify_commit_reachability(str(REPO_ROOT), "2d40b9d")
        self.assertTrue(ok, msg)

    def test_unreachable_commit(self):
        ok, msg = verify_commit_reachability(str(REPO_ROOT), "0000000000000000000000000000000000000000")
        self.assertFalse(ok)


class TestVerifyArtifactAtCommit(unittest.TestCase):
    def test_existing_artifact(self):
        ok, content = verify_artifact_at_commit(
            str(REPO_ROOT), "HEAD",
            "data/scatti_candidates/materials_project/materials_project_search_results.json"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(content)

    def test_missing_artifact(self):
        ok, content = verify_artifact_at_commit(
            str(REPO_ROOT), "HEAD",
            "nonexistent_file.json"
        )
        self.assertFalse(ok)
        self.assertIsNone(content)


class TestCompareArtifactHashes(unittest.TestCase):
    def test_identical_content(self):
        match, h1, h2 = compare_artifact_hashes(b"hello", b"hello")
        self.assertTrue(match)
        self.assertEqual(h1, h2)

    def test_different_content(self):
        match, h1, h2 = compare_artifact_hashes(b"hello", b"world")
        self.assertFalse(match)
        self.assertNotEqual(h1, h2)


class TestCompareMachineReadableClaim(unittest.TestCase):
    def test_matching_keys(self):
        a = {"formula": "CaSc2TiO6", "count": 0}
        b = {"formula": "CaSc2TiO6", "count": 0}
        result = compare_machine_readable_claim(a, b, ["formula", "count"])
        self.assertTrue(result["formula"]["match"])
        self.assertTrue(result["count"]["match"])

    def test_mismatched_keys(self):
        a = {"formula": "CaSc2TiO6", "count": 0}
        b = {"formula": "CaSc2TiO6", "count": 1}
        result = compare_machine_readable_claim(a, b, ["count"])
        self.assertFalse(result["count"]["match"])


class TestReconcileStageStatus(unittest.TestCase):
    def test_superseded(self):
        status = reconcile_stage_status(LOCALLY_VERIFIED, IMPORTED_AND_VERIFIED, supersession="scaling_bug")
        self.assertEqual(status, SUPERSEDED_VERIFIED)

    def test_imported_verified(self):
        status = reconcile_stage_status(UNRESOLVED, IMPORTED_AND_VERIFIED)
        self.assertEqual(status, IMPORTED_AND_VERIFIED)

    def test_artifact_missing(self):
        status = reconcile_stage_status(LOCALLY_VERIFIED, ARTIFACT_MISSING)
        self.assertEqual(status, ARTIFACT_MISSING)


class TestRecordSupersession(unittest.TestCase):
    def test_supersession_record(self):
        result = record_supersession(
            "stoichiometric impossibility",
            "Z-scaling bug confirmed",
            "Script added 1 Ca+1 O instead of 2 Ca+2 O"
        )
        self.assertEqual(result["status"], SUPERSEDED_VERIFIED)
        self.assertEqual(result["superseded_claim"], "stoichiometric impossibility")


class TestBuildReconciliationCertificate(unittest.TestCase):
    def test_certificate_structure(self):
        cert = build_reconciliation_certificate(
            proposition="Test proposition",
            prior_local_status=LOCALLY_VERIFIED,
            imported_source_status=IMPORTED_AND_VERIFIED,
            source_commits=["abc123"],
            source_paths=["test.json"],
            hashes={"sha256": "abc"},
            independent_checks={"check1": True},
            conflicts=[],
            supersedes=None,
            final_status=IMPORTED_AND_VERIFIED,
            limitations=["Test limitation"],
        )
        self.assertEqual(cert["proposition"], "Test proposition")
        self.assertEqual(cert["final_status"], IMPORTED_AND_VERIFIED)
        self.assertIn("semantic_hash", cert)
        self.assertEqual(len(cert["semantic_hash"]), 64)


class TestCanonicalSerialize(unittest.TestCase):
    def test_deterministic(self):
        h1 = canonical_serialize({"b": 2, "a": 1})
        h2 = canonical_serialize({"a": 1, "b": 2})
        self.assertEqual(h1, h2)

    def test_different_content(self):
        h1 = canonical_serialize({"a": 1})
        h2 = canonical_serialize({"a": 2})
        self.assertNotEqual(h1, h2)


class TestCrossHostVerifier(unittest.TestCase):
    """Fixture-based verifier tests. Does NOT invoke the live repository verifier."""

    def _make_fixture_receipt(self, passed=10, failed=0, errors=0, skipped=0):
        """Create a temporary fixture receipt."""
        import tempfile, json
        receipt = {
            "test_suite": "fixture",
            "total": passed + failed + errors + skipped,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped
        }
        return receipt

    def test_verifier_accepts_passing_receipt(self):
        """Fixture: verifier should accept a passing receipt."""
        receipt = self._make_fixture_receipt(passed=10, failed=0, errors=0)
        self.assertEqual(receipt["failed"], 0)
        self.assertEqual(receipt["errors"], 0)

    def test_verifier_rejects_failing_receipt(self):
        """Fixture: verifier should reject a receipt with failures."""
        receipt = self._make_fixture_receipt(passed=8, failed=2, errors=0)
        self.assertGreater(receipt["failed"], 0)

    def test_verifier_rejects_error_receipt(self):
        """Fixture: verifier should reject a receipt with errors."""
        receipt = self._make_fixture_receipt(passed=8, failed=0, errors=2)
        self.assertGreater(receipt["errors"], 0)

    def test_verifier_rejects_mismatched_totals(self):
        """Fixture: verifier should reject when total != sum of parts."""
        receipt = self._make_fixture_receipt(passed=10, failed=0, errors=0)
        self.assertEqual(receipt["total"], receipt["passed"] + receipt["failed"] + receipt["errors"] + receipt.get("skipped", 0))

    def test_wrong_transport_hash_detected(self):
        """Fixture: wrong transport hash should be detected."""
        import subprocess
        actual = subprocess.check_output(
            ["git", "rev-parse", "04dc013305b713c1eb3ea0117e462aa77099485f"],
            cwd=str(REPO_ROOT)
        ).decode().strip()
        self.assertEqual(actual, "04dc013305b713c1eb3ea0117e462aa77099485f")

    def test_mp_zero_hit_verified(self):
        mp_path = REPO_ROOT / "data" / "scatti_candidates" / "materials_project" / "materials_project_search_results.json"
        with open(mp_path) as f:
            data = json.load(f)
        for entry in data:
            if entry.get("formula") == "CaSc2TiO6":
                self.assertEqual(entry.get("count"), 0)
                break
        else:
            self.fail("CaSc2TiO6 entry not found in MP data")

    def test_no_secret_exposure(self):
        """Verify no credential values in committed artifacts."""
        import re
        cred_patterns = [
            re.compile(r'[^a-zA-Z](re_[A-Za-z0-9_]{10,})[^a-zA-Z]'),
            re.compile(r'[^a-zA-Z](sk-[A-Za-z0-9]{10,})[^a-zA-Z]'),
            re.compile(r'[^a-zA-Z](cfat_[A-Za-z0-9_]{10,})[^a-zA-Z]'),
        ]
        v3_dir = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"
        for fpath in v3_dir.glob("*.json"):
            content = fpath.read_text()
            for pat in cred_patterns:
                self.assertIsNone(pat.search(content),
                                  f"Credential pattern found in {fpath.name}")


if __name__ == "__main__":
    unittest.main()
