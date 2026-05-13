from __future__ import annotations

import json
import subprocess
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.provenance_source_registry import (  # noqa: E402
    PROHIBITED_SAFETY_FLAG_FIELDS,
    ProvenanceSourceEntry,
    validate_provenance_source_entry,
)
from weslr.provenance_source_registry_seed import (  # noqa: E402
    load_initial_provenance_source_entries_v1,
    summarize_initial_provenance_source_seed_v1,
    summary_initial_provenance_source_seed_v1,
    validate_initial_provenance_source_seed_v1,
)

ALLOWED_CHANGED = {
    "weslr/provenance_source_registry_seed.py",
    "weslr/tests/test_provenance_source_registry_initial_seed_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}
REQUIRED_SOURCE_IDS = {
    "capability_registry",
    "proactive_suggestions",
    "voice_gateway",
    "ambient_voice_loop",
    "llm_advisor_mode",
    "advisor_review_queue",
    "local_scan_advisor_review",
    "synthetic_teaching_lane",
    "output_provenance",
    "provenance_source_registry",
}
PROHIBITED_SUMMARY_STRINGS = [
    "api key",
    "token",
    "secret",
    "raw benchmark",
    "answer key",
    "private user data",
]
FORBIDDEN_ARTIFACTS = [
    ROOT / ".weslr" / "advisor_review_queue.jsonl",
    ROOT / ".weslr" / "provenance_source_registry.json",
    ROOT / ".weslr" / "provenance_source_registry.jsonl",
]


class ProvenanceSourceRegistryInitialSeedV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load_initial_provenance_source_entries_v1()
        cls.by_id = {entry.source_id: entry for entry in cls.entries}
        cls.summary = summarize_initial_provenance_source_seed_v1()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(load_initial_provenance_source_entries_v1)
        self.assertTrue(summarize_initial_provenance_source_seed_v1)
        self.assertTrue(summary_initial_provenance_source_seed_v1)
        self.assertTrue(validate_initial_provenance_source_seed_v1)

    def test_02_seed_loader_returns_list(self):
        self.assertIsInstance(self.entries, list)

    def test_03_seed_has_at_least_10_entries(self):
        self.assertGreaterEqual(len(self.entries), 10)

    def test_04_all_entries_are_provenance_source_entries(self):
        self.assertTrue(all(isinstance(entry, ProvenanceSourceEntry) for entry in self.entries))

    def test_05_all_entries_validate(self):
        self.assertEqual([], validate_initial_provenance_source_seed_v1())
        for entry in self.entries:
            self.assertEqual([], validate_provenance_source_entry(entry), entry.source_id)

    def test_06_source_ids_are_unique(self):
        source_ids = [entry.source_id for entry in self.entries]
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_07_seed_includes_capability_registry(self):
        self.assertIn("capability_registry", self.by_id)

    def test_08_seed_includes_proactive_suggestions(self):
        self.assertIn("proactive_suggestions", self.by_id)

    def test_09_seed_includes_voice_gateway(self):
        self.assertIn("voice_gateway", self.by_id)

    def test_10_seed_includes_ambient_voice_loop(self):
        self.assertIn("ambient_voice_loop", self.by_id)

    def test_11_seed_includes_llm_advisor_mode(self):
        self.assertIn("llm_advisor_mode", self.by_id)

    def test_12_seed_includes_advisor_review_queue(self):
        self.assertIn("advisor_review_queue", self.by_id)

    def test_13_seed_includes_local_scan_advisor_review(self):
        self.assertIn("local_scan_advisor_review", self.by_id)

    def test_14_seed_includes_synthetic_teaching_lane(self):
        self.assertIn("synthetic_teaching_lane", self.by_id)

    def test_15_seed_includes_output_provenance(self):
        self.assertIn("output_provenance", self.by_id)

    def test_16_seed_includes_provenance_source_registry(self):
        self.assertIn("provenance_source_registry", self.by_id)

    def test_17_every_entry_has_authority_boundary(self):
        self.assertTrue(all(entry.authority_boundary.strip() for entry in self.entries))

    def test_18_every_entry_has_allowed_outputs(self):
        self.assertTrue(all(entry.allowed_outputs for entry in self.entries))

    def test_19_every_entry_has_forbidden_outputs(self):
        self.assertTrue(all(entry.forbidden_outputs for entry in self.entries))

    def test_20_every_entry_requires_operator_review(self):
        self.assertTrue(all(entry.operator_review_required for entry in self.entries))

    def test_21_every_entry_requires_validation(self):
        self.assertTrue(all(entry.validation_required for entry in self.entries))

    def test_22_every_entry_requires_tests(self):
        self.assertTrue(all(entry.tests_required for entry in self.entries))

    def test_23_no_entry_has_unsafe_safety_flags(self):
        for entry in self.entries:
            for field in fields(entry.safety_flags):
                self.assertFalse(getattr(entry.safety_flags, field.name), f"{entry.source_id}:{field.name}")
            for field_name in PROHIBITED_SAFETY_FLAG_FIELDS:
                self.assertFalse(getattr(entry.safety_flags, field_name), f"{entry.source_id}:{field_name}")

    def test_24_no_self_improvement_entry_auto_activates(self):
        for entry in self.entries:
            if entry.origin_type == "self_improvement_proposed" or entry.source_type == "self_improvement_candidate":
                self.assertFalse(entry.activation_allowed)
        self.assertTrue(all(not entry.activation_allowed for entry in self.entries))

    def test_25_no_entry_claims_truth_or_soundness_authority(self):
        for entry in self.entries:
            self.assertFalse(entry.safety_flags.truth_authority_allowed)
            self.assertFalse(entry.safety_flags.soundness_authority_allowed)
            self.assertNotIn("truth authority", " ".join(entry.allowed_outputs).lower())
            self.assertNotIn("soundness authority", " ".join(entry.allowed_outputs).lower())

    def test_26_no_entry_claims_benchmark_authority(self):
        for entry in self.entries:
            self.assertFalse(entry.safety_flags.official_score_claim_allowed)
            self.assertNotIn("benchmark authority", " ".join(entry.allowed_outputs).lower())

    def assert_count_only(self, value: Any):
        if isinstance(value, dict):
            for key, nested in value.items():
                self.assertIsInstance(key, str)
                self.assert_count_only(nested)
        elif isinstance(value, list):
            for nested in value:
                self.assert_count_only(nested)
        else:
            self.assertIsInstance(value, (int, str))

    def test_27_summary_is_redacted_count_only(self):
        self.assertEqual("redacted_count_only", self.summary["summary_mode"])
        self.assertNotIn("source_ids", self.summary)
        self.assertNotIn("display_names", self.summary)
        self.assertNotIn("authority_boundaries", self.summary)
        self.assertNotIn("allowed_outputs", self.summary)
        self.assertNotIn("forbidden_outputs", self.summary)
        self.assert_count_only(self.summary)
        self.assertEqual(self.summary, summary_initial_provenance_source_seed_v1())

    def test_28_summary_avoids_sensitive_raw_text_markers(self):
        rendered = json.dumps(self.summary, sort_keys=True).lower()
        for phrase in PROHIBITED_SUMMARY_STRINGS:
            self.assertNotIn(phrase, rendered)

    def test_29_registry_schema_tests_still_pass_clean_tree_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_provenance_source_registry_schema_v1.py").exists())

    def test_30_lifecycle_design_tests_still_pass_clean_tree_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_provenance_source_registry_lifecycle_design_v1.py").exists())

    def test_31_output_provenance_envelope_tests_still_pass_clean_tree_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_output_provenance_envelope_schema_v1.py").exists())

    def test_32_release_gate_and_check_are_available(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "release_gate_v1.py").exists())
        self.assertTrue((ROOT / "scripts" / "weslr_release_check.sh").exists())

    def test_33_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_34_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_35_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")

    def test_36_seed_includes_required_source_ids(self):
        self.assertTrue(REQUIRED_SOURCE_IDS <= set(self.by_id))

    def test_37_summary_counts_match_seed(self):
        self.assertEqual(len(self.entries), self.summary["total_entries"])
        self.assertEqual(len(self.entries), self.summary["operator_review_required_count"])
        self.assertEqual(0, self.summary["activation_allowed_count"])
        self.assertEqual(0, self.summary["invalid_entry_count"])
        self.assertEqual(0, self.summary["unsafe_safety_flag_count"])
        self.assertEqual(0, self.summary["missing_docs_count"])
        self.assertEqual(0, self.summary["missing_tests_count"])

    def test_38_seed_does_not_create_forbidden_artifacts(self):
        load_initial_provenance_source_entries_v1()
        summarize_initial_provenance_source_seed_v1()
        validate_initial_provenance_source_seed_v1()
        for path in FORBIDDEN_ARTIFACTS:
            self.assertFalse(path.exists(), str(path))


if __name__ == "__main__":
    unittest.main()
