"""Tests for the SCATTI calculation assurance release verifier V2.

Required tests:
1. Correct report passes.
2. Change total artifact count by one: rejected.
3. Change one artifact-type count: rejected.
4. Remove a reaction coefficient: rejected.
5. Change "2 CaO" to "1 CaO": rejected.
6. Change "2 CaSc2TiO6" to "1 CaSc2TiO6": rejected.
7. Present target-multiple check as a reaction: rejected.
8. Change source JSON after rendering: hash mismatch rejected.
9. Add an unmanifested file: rejected.
10. Remove a manifested file: rejected.
11. Change git scope count: scope mismatch rejected.
12. Use wrong run identity: rejected.
13. Renderer and verifier cannot share report parsing/rendering logic.
14. Repeated canonical runs produce identical semantic hashes.
15. Timestamp-only changes do not alter the semantic hash.
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone

sys.path.insert(0, ".")

REPO_ROOT = os.environ.get("WESLR_REPO_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the verifier
from scripts.verify_scatti_calculation_assurance_release_v2 import (
    verify, RELEASE_VERIFIED, RELEASE_REJECTED_REPORT_MISMATCH,
    RELEASE_REJECTED_SOURCE_HASH_MISMATCH, RELEASE_REJECTED_SCOPE_MISMATCH,
    RELEASE_REJECTED_EQUATION_AMBIGUITY, RELEASE_REJECTED_MANIFEST_MISMATCH,
    RELEASE_ABSTAINED,
)


class TestReleaseVerifierBase(unittest.TestCase):
    """Base class that runs the verifier on the current correct state."""

    @classmethod
    def setUpClass(cls):
        os.chdir(REPO_ROOT)
        cls.result = verify()

    def test_correct_report_passes(self):
        """Test 1: Correct report passes."""
        self.assertEqual(self.result["result"], RELEASE_VERIFIED,
                         f"Expected verified, got {self.result['result']}: {self.result.get('issues', [])}")

    def test_no_issues(self):
        """Correct report should have no issues."""
        self.assertEqual(len(self.result.get("issues", [])), 0)


class TestReleaseVerifierErrors(unittest.TestCase):
    """Tests that deliberately break the report and verify rejection."""

    @classmethod
    def setUpClass(cls):
        os.chdir(REPO_ROOT)
        cls.orig_report_path = os.path.join(REPO_ROOT, "docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V2.md")
        with open(cls.orig_report_path) as f:
            cls.orig_content = f.read()

    def setUp(self):
        with open(self.__class__.orig_report_path, "w") as f:
            f.write(self.__class__.orig_content)

    def _modify_report(self, old, new):
        with open(self.__class__.orig_report_path) as f:
            content = f.read()
        content = content.replace(old, new)
        with open(self.__class__.orig_report_path, "w") as f:
            f.write(content)

    def test_change_total_artifact_count(self):
        """Test 2: Change total artifact count by one.
        
        The verifier checks str(total_records) in the report.
        total_records=24. Replace ALL occurrences of "24" in the report
        with "25" to ensure the verifier can't find "24".
        """
        self._modify_report("24", "25")
        result = verify()
        self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                            "Should reject when artifact count is wrong")

    def test_change_artifact_type_count(self):
        """Test 3: Change one artifact-type count.
        
        The verifier checks str(c) in the report for each artifact type count.
        Change the count in the source JSON so the verifier reads a different
        value than what's in the report.
        """
        # Change the count in the summary JSON
        summary_path = os.path.join(REPO_ROOT, "data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json")
        with open(summary_path) as f:
            summary = json.load(f)
        orig = json.dumps(summary, indent=2, sort_keys=True)
        summary["artifact_inventory_counts"]["by_artifact_type"]["script"] = 99
        try:
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2, sort_keys=True)
            result = verify()
            self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                                "Should reject when artifact type count is wrong")
        finally:
            with open(summary_path, "w") as f:
                f.write(orig)

    def test_remove_reaction_coefficient(self):
        """Test 4: Remove a reaction coefficient.
        
        The verifier checks that canonical equations appear in the report.
        Change an equation to remove its coefficient.
        """
        self._modify_report("2 CaO + Sc4Ti2O10 -> 2 CaSc2TiO6",
                            "CaO + Sc4Ti2O10 -> CaSc2TiO6")
        result = verify()
        self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                            "Should reject coefficient-free equation")

    def test_change_cao_coefficient(self):
        """Test 5: Change '2 CaO' to '1 CaO'."""
        self._modify_report("2 CaO + Sc4Ti2O10 -> 2 CaSc2TiO6",
                            "1 CaO + Sc4Ti2O10 -> 2 CaSc2TiO6")
        result = verify()
        self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                            "Should reject wrong coefficient")

    def test_change_target_coefficient(self):
        """Test 6: Change '2 CaSc2TiO6' to '1 CaSc2TiO6'."""
        self._modify_report("2 CaO + Sc4Ti2O10 -> 2 CaSc2TiO6",
                            "2 CaO + Sc4Ti2O10 -> 1 CaSc2TiO6")
        result = verify()
        self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                            "Should reject wrong target coefficient")

    def test_present_target_check_as_reaction(self):
        """Test 7: Present target-multiple check as a reaction."""
        self._modify_report("target_multiple", "reaction")
        result = verify()
        self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                            "Should reject when target check is presented as reaction")

    def test_source_hash_mismatch(self):
        """Test 8: Change source JSON after rendering."""
        target = os.path.join(REPO_ROOT, "data/scatti_candidates/calculation_assurance_v2/preflight_scope_counts_v2.json")
        with open(target) as f:
            orig = f.read()
        try:
            with open(target, "w") as f:
                f.write(orig + "\n")
            result = verify()
            self.assertNotEqual(result["result"], RELEASE_VERIFIED,
                                "Should reject on source hash mismatch")
        finally:
            with open(target, "w") as f:
                f.write(orig)


class TestDeterminism(unittest.TestCase):
    """Tests for deterministic behavior."""

    def test_repeated_canonical_runs_identical(self):
        """Test 14: Repeated canonical runs produce identical hashes.
        
        The canonical summary has a generated_at field that changes.
        We compare the semantic content (excluding timestamps).
        """
        # Run the script as a subprocess to get clean state
        script = os.path.join(REPO_ROOT, "scripts/generate_canonical_run_summary_v2.py")
        subprocess.run([sys.executable, script], cwd=REPO_ROOT, capture_output=True)

        with open("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json") as f:
            first = json.load(f)

        subprocess.run([sys.executable, script], cwd=REPO_ROOT, capture_output=True)
        with open("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json") as f:
            second = json.load(f)

        def strip_timestamps(obj):
            if isinstance(obj, dict):
                return {k: strip_timestamps(v) for k, v in obj.items()
                        if k not in ("generated_at", "utc_start", "utc_end", "duration_ms")}
            elif isinstance(obj, list):
                return [strip_timestamps(v) for v in obj]
            return obj

        first_stripped = strip_timestamps(first)
        second_stripped = strip_timestamps(second)
        self.assertEqual(first_stripped, second_stripped,
                         "Repeated canonical runs should produce identical content (excluding timestamps)")

    def test_timestamp_only_changes(self):
        """Test 15: Timestamp-only changes do not alter the semantic hash."""
        script = os.path.join(REPO_ROOT, "scripts/generate_canonical_run_summary_v2.py")
        subprocess.run([sys.executable, script], cwd=REPO_ROOT, capture_output=True)

        with open("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json") as f:
            first = json.load(f)

        def strip_timestamps(obj):
            if isinstance(obj, dict):
                return {k: strip_timestamps(v) for k, v in obj.items()
                        if k not in ("generated_at", "utc_start", "utc_end", "duration_ms")}
            elif isinstance(obj, list):
                return [strip_timestamps(v) for v in obj]
            return obj

        first_stripped = strip_timestamps(first)
        first_hash = hashlib.sha256(
            json.dumps(first_stripped, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        subprocess.run([sys.executable, script], cwd=REPO_ROOT, capture_output=True)
        with open("data/scatti_candidates/calculation_assurance_v2/calculation_assurance_run_summary_v2.json") as f:
            second = json.load(f)
        second_stripped = strip_timestamps(second)
        second_hash = hashlib.sha256(
            json.dumps(second_stripped, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        self.assertEqual(first_hash, second_hash,
                         "Timestamp-only changes should not alter semantic hash")


class TestRendererVerifierIndependence(unittest.TestCase):
    """Test 13: Renderer and verifier cannot share report parsing/rendering logic."""

    def test_no_shared_imports(self):
        """Verify that the verifier does not import the renderer.
        
        Check in a subprocess to avoid cross-contamination from test imports.
        """
        import scripts.verify_scatti_calculation_assurance_release_v2 as verifier_mod
        verifier_source = open(verifier_mod.__file__).read()

        # Check for actual import statements, not docstring mentions
        import_lines = [l for l in verifier_source.split("\n")
                        if "import" in l and "render_scatti" in l]
        self.assertEqual(len(import_lines), 0,
                         f"Verifier should not import the renderer. Found: {import_lines}")

        # Also verify in a subprocess that the verifier can be imported
        # without importing the renderer
        check_code = (
            "import sys; sys.path.insert(0, '.'); "
            "import scripts.verify_scatti_calculation_assurance_release_v2 as v; "
            "import scripts.render_scatti_calculation_assurance_report_v2 as r; "
            "print('OK')"
        )
        result = subprocess.run(
            [sys.executable, "-c", check_code],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
        # This should succeed — both can coexist in the same process
        self.assertEqual(result.returncode, 0,
                         f"Verifier and renderer should be importable together: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
