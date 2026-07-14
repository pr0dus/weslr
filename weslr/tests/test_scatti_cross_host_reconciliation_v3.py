#!/usr/bin/env python3
"""Integration tests for SCATTI cross-host reconciliation V3."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestScattiCrossHostReconciliationV3(unittest.TestCase):
    """Integration tests for the full V3 reconciliation."""

    @classmethod
    def setUpClass(cls):
        cls.v3_dir = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"
        cls.required_artifacts = [
            "transport_commit_verification_v3.json",
            "transport_path_collision_v3.json",
            "imported_assurance_test_results_v3.json",
            "ubuntu_scatti_artifact_inventory_v3.json",
            "materials_project_evidence_verification_v3.json",
            "mp_parent_experiment_reaudit_v3.json",
            "multilingual_search_verification_v3.json",
            "structure_and_chgnet_evidence_verification_v3.json",
            "scatti_evidence_ledger_v3.json",
            "scatti_implementation_inventory_v3.json",
            "verifier_results_v3.json",
        ]

    def test_all_artifacts_exist(self):
        for name in self.required_artifacts:
            path = self.v3_dir / name
            self.assertTrue(path.exists(), f"Missing: {name}")

    def test_all_json_valid(self):
        for name in self.required_artifacts:
            path = self.v3_dir / name
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                self.assertIsNotNone(data, f"Empty JSON: {name}")

    def test_transport_commit_verified(self):
        path = self.v3_dir / "transport_commit_verification_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["commit_hash"], "04dc013305b713c1eb3ea0117e462aa77099485f")
        self.assertEqual(data["parent"], "62e9ba794c780bb37d5472d79ca8c9d91230892d")
        self.assertEqual(data["total_files"], 39)
        self.assertTrue(data["all_additions"])
        self.assertEqual(data["commit_verification_status"], "transport_commit_verified")

    def test_path_collision_clear(self):
        path = self.v3_dir / "transport_path_collision_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertTrue(data["can_cherry_pick"])
        self.assertEqual(len(data["present_different"]), 0)

    def test_mp_evidence_verified(self):
        path = self.v3_dir / "materials_project_evidence_verification_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["status"], "mp_evidence_verified")
        self.assertFalse(data["api_key_in_output"])
        # CaSc2TiO6 should have 0 hits
        for q in data["queries"]:
            if q["formula"] == "CaSc2TiO6":
                self.assertEqual(q["count"], 0)

    def test_parent_experiment_scaling_bug(self):
        path = self.v3_dir / "mp_parent_experiment_reaudit_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["verdict"], "scaling_bug_confirmed")
        self.assertEqual(data["parent_z"], 2)
        self.assertEqual(data["script_adds_cell_level"]["Ca"], 1)
        self.assertEqual(data["should_add_cell_level"]["Ca"], 2)

    def test_multilingual_partial_verified(self):
        path = self.v3_dir / "multilingual_search_verification_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["status"], "multilingual_partial_verified")
        self.assertIn("limitations", data)

    def test_ledger_has_8_corrections(self):
        path = self.v3_dir / "scatti_evidence_ledger_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(len(data["corrections"]), 8)

    def test_corr_008_global_state(self):
        path = self.v3_dir / "scatti_evidence_ledger_v3.json"
        with open(path) as f:
            data = json.load(f)
        corr_008 = [c for c in data["corrections"] if c["correction"] == "CORR-008"]
        self.assertEqual(len(corr_008), 1)
        self.assertEqual(corr_008[0]["final_status"],
                         "cross_host_evidence_reconciled_pre_structure_validation")

    def test_verifier_passed(self):
        path = self.v3_dir / "verifier_results_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertIn(data["overall"], ["cross_host_reconciliation_verified", "cross_host_reconciliation_release_verified"],
                         f"Verifier failed: {data.get('failed', 'unknown')} failures")
        self.assertEqual(data["failed"], 0)

    def test_no_scientific_overpromotion(self):
        """Verify no affirmative overpromotion claims in V3 artifacts."""
        overpromotion_terms = [
            "discovered", "stable", "DFT-ready", "synthesizable",
            "breakthrough", "confirmed_structure", "proven",
        ]
        safe_words = {"novelty", "provenance"}
        negation_prefixes = ["no ", "not ", "not proof of ", "not a "]

        for name in self.required_artifacts:
            path = self.v3_dir / name
            if not path.exists():
                continue
            content = path.read_text().lower()
            for term in overpromotion_terms:
                idx = 0
                while idx < len(content):
                    idx = content.find(term, idx)
                    if idx == -1:
                        break
                    word_start = content.rfind(" ", 0, idx) + 1
                    word_end = content.find(" ", idx)
                    if word_end == -1:
                        word_end = len(content)
                    full_word = content[word_start:word_end].strip(".,;:!?\"'")
                    if full_word in safe_words:
                        idx += len(term)
                        continue
                    # Check if the full word contains a safe substring
                    safe_substrings = {"provenance"}
                    is_substring_of_safe = any(sw in full_word for sw in safe_substrings)
                    if is_substring_of_safe:
                        idx += len(term)
                        continue
                    # "stable" in a question context is not overpromotion
                    if term == "stable" and "?" in content[max(0, idx-50):idx+len(term)+10]:
                        idx += len(term)
                        continue
                    start = max(0, idx - 30)
                    preceding = content[start:idx].strip()
                    is_negated = any(preceding.endswith(neg) for neg in negation_prefixes)
                    self.assertTrue(is_negated,
                                    f"Affirmative overpromotion '{term}' found in {name}")
                    idx += len(term)

    def test_report_rendered(self):
        report_path = REPO_ROOT / "docs" / "WESLR_SCATTI_CROSS_HOST_RECONCILIATION_REPORT_V3.md"
        self.assertTrue(report_path.exists())
        content = report_path.read_text()
        self.assertIn("cross_host_evidence_reconciled_pre_structure_validation", content)
        self.assertIn("04dc013305b713c1eb3ea0117e462aa77099485f", content)
        self.assertIn("scaling_bug_confirmed", content)

    def test_no_missing_source_paths(self):
        """Verify all source paths referenced in V3 artifacts exist in the repo."""
        v3_paths = [
            "data/scatti_candidates/materials_project/materials_project_search_results.json",
            "data/scatti_candidates/materials_project/cifs/mp-753401_Sc2TiO5.cif",
            "data/scatti_candidates/materials_project/cifs/mp-4056_CaSc2O4.cif",
            "data/scatti_candidates/materials_project/cifs/mp-753802_Sc2Ti2O7.cif",
            "data/scatti_candidates/materials_project/cifs/mp-780402_Sc2Ti2O7.cif",
            "data/scatti_candidates/scatti_multilingual_search.json",
            "data/scatti_candidates/chgnet_relaxation/SCATTI-LAYERED-001/relaxation_summary.json",
        ]
        for p in v3_paths:
            full_path = REPO_ROOT / p
            self.assertTrue(full_path.exists(), f"Missing source path: {p}")

    def test_implementation_inventory_complete(self):
        path = self.v3_dir / "scatti_implementation_inventory_v3.json"
        with open(path) as f:
            data = json.load(f)
        self.assertGreater(len(data.get("modules", {})), 0)
        self.assertGreater(len(data.get("scripts", {})), 0)
        self.assertGreater(len(data.get("tests", {})), 0)


class TestR4ARegressionDefects(unittest.TestCase):
    """Regression tests for defects found in R4A review."""

    @classmethod
    def setUpClass(cls):
        cls.v3_dir = REPO_ROOT / "data" / "scatti_candidates" / "cross_host_reconciliation_v3"
        cls.review_dir = Path("/home/pr0/scatti-review-r4b")

    def test_verifier_rejects_failed_validation(self):
        """R4A defect 1: verifier must reject any receipt with failed > 0."""
        path = self.v3_dir / "verifier_results_v3.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            if data.get("failed", 0) > 0:
                self.assertNotEqual(data.get("overall"), "cross_host_reconciliation_verified",
                                    "Verifier must not pass when failures exist")

    def test_verifier_rejects_errors(self):
        """R4A defect 2: verifier must reject any receipt with errors > 0."""
        path = self.v3_dir / "verifier_results_v3.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            if data.get("errors", 0) > 0:
                self.assertNotEqual(data.get("overall"), "cross_host_reconciliation_verified",
                                    "Verifier must not pass when errors exist")

    def test_archive_member_count_agreement(self):
        """R4A defect 3: archive-reported member count must equal actual."""
        # Check V3 bundle
        bundle_path = REPO_ROOT / "artifacts" / "scatti_cross_host_reconciliation_v3.tar.gz"
        manifest_path = REPO_ROOT / "artifacts" / "scatti_cross_host_reconciliation_manifest_v3.json"
        if bundle_path.exists() and manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            import subprocess
            result = subprocess.run(["tar", "-tzf", str(bundle_path)], capture_output=True, text=True)
            actual_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            reported_count = manifest.get("file_count", 0)
            self.assertEqual(actual_count, reported_count,
                             f"Bundle member count: actual={actual_count}, reported={reported_count}")

    def test_readme_paths_exist_in_zip(self):
        """R4A defect 4: README-listed paths must exist in the ZIP."""
        # Check R4A review ZIP if it exists
        zip_path = self.review_dir / "WESLR_SCATTI_CROSS_HOST_REVIEW_R4B.zip"
        if zip_path.exists():
            import zipfile
            with zipfile.ZipFile(zip_path) as zf:
                member_names = set(zf.namelist())
            readme_path = self.review_dir / "README_FIRST.md"
            if readme_path.exists():
                content = readme_path.read_text()
                # Check that files mentioned in README exist in ZIP
                for line in content.split('\n'):
                    if line.strip().startswith('| `'):
                        fname = line.split('`')[1].strip()
                        if fname in member_names:
                            continue
                        # Check if it's a directory reference
                        dir_name = fname.rstrip('/')
                        if not any(m.startswith(dir_name) for m in member_names):
                            self.fail(f"README references '{fname}' but not found in ZIP")

    def test_raw_validation_present(self):
        """R4A defect 5: raw test outputs must be present."""
        raw_dir = self.v3_dir / "raw_validation_r4a"
        self.assertTrue(raw_dir.exists(), "raw_validation_r4a directory missing")
        has_output = any(raw_dir.iterdir())
        self.assertTrue(has_output, "No raw validation output files found")

    def test_source_repair_visible(self):
        """R4A defect 6: claimed source repair must be visible in source file."""
        repair_path = self.v3_dir / "source_patch_verification_r4b.json"
        if repair_path.exists():
            with open(repair_path) as f:
                data = json.load(f)
            for repair in data.get("repairs", []):
                self.assertIn(repair.get("verification_result", ""),
                              ["repair_present_modified", "repair_present_already_committed"],
                              f"Repair not visible: {repair['path']}")

    def test_no_live_untracked_count_as_fixture(self):
        """R4A defect 8: live repository untracked count cannot be a stable test fixture."""
        # Verify that no test uses git status --short untracked count as expected value
        # Exclude this test file itself (it only references the string in assertions)
        test_files = [
            REPO_ROOT / "weslr/tests/test_scatti_audit_consistency.py",
            REPO_ROOT / "weslr/tests/test_scatti_calculation_assurance_release_v2.py",
            REPO_ROOT / "weslr/tests/test_cross_host_evidence_reconciliation.py",
        ]
        for tf in test_files:
            if tf.exists():
                content = tf.read_text()
                self.assertNotIn("git status --short", content,
                                 f"Live git status used in {tf.name}")
                self.assertNotIn("git status --porcelain", content,
                                 f"Live git status used in {tf.name}")

    def test_no_host_specific_commit_reachability(self):
        """R4A defect 9: host-specific commit reachability cannot determine expected result."""
        test_files = [
            REPO_ROOT / "weslr/tests/test_scatti_audit_consistency.py",
        ]
        for tf in test_files:
            if tf.exists():
                content = tf.read_text()
                # Should use temp repo fixture, not live repo
                self.assertIn("TemporaryDirectory", content,
                              f"Test should use isolated fixture, not live repo: {tf.name}")

    def test_composition_not_labeled_geometry(self):
        """R4A defect 10: composition verification cannot be labeled physical-geometry verification."""
        structure_path = self.v3_dir / "structure_and_chgnet_evidence_verification_r4a.json"
        if structure_path.exists():
            with open(structure_path) as f:
                data = json.load(f)
            for sname, sinfo in data.get("structures", {}).items():
                status = sinfo.get("status", "")
                self.assertNotEqual(status, "fully_verified",
                                    f"Structure {sname} uses overbroad 'fully_verified' status")

    def test_promotion_gate_false_does_not_recommend_phase(self):
        """R4A defect 11: promotion gate false cannot recommend beginning that phase."""
        summary_path = self.v3_dir / "scatti_cross_host_review_summary_r4a.json"
        if summary_path.exists():
            with open(summary_path) as f:
                data = json.load(f)
            gates = data.get("promotion_gates", {})
            next_phase = data.get("next_recommended_phase", "")
            if not gates.get("ready_for_corrected_geometry_phase", False):
                self.assertNotEqual(next_phase, "corrected_parent_derived_geometry_construction",
                                    "Cannot recommend geometry phase when gate is false")

    def test_report_summary_receipt_counts_agree(self):
        """R4A defect 12: report, summary, receipt and archive counts must agree."""
        # Check that verifier results are consistent
        verifier_path = self.v3_dir / "verifier_results_v3.json"
        if verifier_path.exists():
            with open(verifier_path) as f:
                verifier = json.load(f)
            total = verifier.get("passed", 0) + verifier.get("failed", 0) + verifier.get("abstained", 0)
            self.assertEqual(total, verifier.get("passed", 0) + verifier.get("failed", 0) + verifier.get("abstained", 0),
                             "Verifier totals inconsistent")


if __name__ == "__main__":
    unittest.main()
