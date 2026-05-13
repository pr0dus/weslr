from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.unregistered_source_detection import (  # noqa: E402
    ALLOWED_AUTHORITY_LEVELS,
    ALLOWED_CANDIDATE_SOURCE_TYPES,
    ALLOWED_DETECTION_SIGNALS,
    ALLOWED_FINDING_TYPES,
    ALLOWED_RISK_LEVELS,
    ALLOWED_SCAN_MODES,
    UnregisteredSourceDetectionReport,
    UnregisteredSourceDetectionSafetyFlags,
    UnregisteredSourceFinding,
    create_empty_unregistered_source_detection_report,
    create_empty_unregistered_source_finding,
    summarize_unregistered_source_detection_report,
    summarize_unregistered_source_finding,
    unregistered_source_detection_report_from_dict,
    unregistered_source_detection_report_to_dict,
    unregistered_source_finding_from_dict,
    unregistered_source_finding_to_dict,
    validate_unregistered_source_detection_report,
    validate_unregistered_source_finding,
)

ALLOWED_CHANGED = {
    "weslr/unregistered_source_detection.py",
    "weslr/tests/test_unregistered_source_detection_schema_v1.py",
    "weslr/tests/test_unregistered_source_detection_helpers_v1.py",
}
FORBIDDEN_CHANGED = {
    "docs/WESLR_UNREGISTERED_SOURCE_DETECTION_DESIGN_V1.md",
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/provenance_source_registry_seed.py",
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
PROHIBITED_SUMMARY_MARKERS = ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]


def valid_finding(**overrides):
    item = create_empty_unregistered_source_finding(
        finding_id="finding_001",
        candidate_source_id="new_source",
        finding_type="unregistered_source_candidate",
        candidate_module_path="weslr.new_source",
        candidate_source_type="self_review",
        detection_signal="module_name_output_like",
        evidence_summary="module name appears source relevant",
        authority_level="unknown",
        operator_review_required=True,
        recommended_action="review source registration need",
        risk_level="low",
        related_docs=["docs/WESLR_UNREGISTERED_SOURCE_DETECTION_DESIGN_V1.md"],
        related_tests=["weslr/tests/test_unregistered_source_detection_schema_v1.py"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_report(**overrides):
    finding = valid_finding()
    item = create_empty_unregistered_source_detection_report(
        report_id="report_001",
        findings=[finding],
        registry_seed_entry_count=20,
        summary="one finding requires operator review",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class UnregisteredSourceDetectionSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(UnregisteredSourceFinding)
        self.assertTrue(UnregisteredSourceDetectionReport)
        self.assertTrue(UnregisteredSourceDetectionSafetyFlags)

    def test_02_empty_finding_instantiates(self):
        item = UnregisteredSourceFinding()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, UnregisteredSourceDetectionSafetyFlags)

    def test_03_empty_report_instantiates(self):
        item = UnregisteredSourceDetectionReport()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, UnregisteredSourceDetectionSafetyFlags)

    def test_04_safe_defaults(self):
        finding = create_empty_unregistered_source_finding()
        report = create_empty_unregistered_source_detection_report()
        self.assertTrue(finding.operator_review_required)
        self.assertFalse(finding.is_registered)
        self.assertEqual("unknown", finding.authority_level)
        self.assertFalse(report.auto_registration_performed)
        self.assertFalse(report.queue_writes_performed)
        self.assertFalse(report.runtime_changes_performed)
        self.assertFalse(report.external_model_calls_performed)

    def test_05_all_finding_types_validate(self):
        for value in ALLOWED_FINDING_TYPES:
            candidate = "source" if value in {"unregistered_source_candidate", "missing_source_registry_entry", "unregistered_voice_or_proactive_source", "unregistered_self_improvement_source"} else ""
            self.assertNotIn("invalid finding_type", validate_unregistered_source_finding(valid_finding(finding_type=value, candidate_source_id=candidate or "source")))

    def test_06_invalid_finding_type_fails(self):
        self.assertIn("invalid finding_type", validate_unregistered_source_finding(valid_finding(finding_type="bad")))

    def test_07_all_detection_signals_validate(self):
        for value in ALLOWED_DETECTION_SIGNALS:
            self.assertNotIn("invalid detection_signal", validate_unregistered_source_finding(valid_finding(detection_signal=value)))

    def test_08_invalid_detection_signal_fails(self):
        self.assertIn("invalid detection_signal", validate_unregistered_source_finding(valid_finding(detection_signal="bad")))

    def test_09_all_candidate_source_types_validate(self):
        for value in ALLOWED_CANDIDATE_SOURCE_TYPES:
            self.assertNotIn("invalid candidate_source_type", validate_unregistered_source_finding(valid_finding(candidate_source_type=value)))

    def test_10_invalid_candidate_source_type_fails(self):
        self.assertIn("invalid candidate_source_type", validate_unregistered_source_finding(valid_finding(candidate_source_type="bad")))

    def test_11_all_authority_levels_validate(self):
        for value in ALLOWED_AUTHORITY_LEVELS:
            item = valid_finding(authority_level=value)
            if value == "advisor_proposal":
                item.is_registered = True
            self.assertNotIn("invalid authority_level", validate_unregistered_source_finding(item))

    def test_12_invalid_authority_level_fails(self):
        self.assertIn("invalid authority_level", validate_unregistered_source_finding(valid_finding(authority_level="bad")))

    def test_13_all_risk_levels_validate(self):
        for value in ALLOWED_RISK_LEVELS:
            self.assertNotIn("invalid risk_level", validate_unregistered_source_finding(valid_finding(risk_level=value)))

    def test_14_invalid_risk_level_fails(self):
        self.assertIn("invalid risk_level", validate_unregistered_source_finding(valid_finding(risk_level="bad")))

    def test_15_all_scan_modes_validate(self):
        for value in ALLOWED_SCAN_MODES:
            self.assertNotIn("invalid scan_mode", validate_unregistered_source_detection_report(valid_report(scan_mode=value)))

    def test_16_invalid_scan_mode_fails(self):
        self.assertIn("invalid scan_mode", validate_unregistered_source_detection_report(valid_report(scan_mode="bad")))

    def test_17_missing_finding_id_fails(self):
        self.assertIn("missing finding_id", validate_unregistered_source_finding(valid_finding(finding_id="")))

    def test_18_missing_candidate_source_id_fails_for_unregistered_source_candidate(self):
        self.assertIn("missing candidate_source_id", validate_unregistered_source_finding(valid_finding(candidate_source_id="")))

    def test_19_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required must remain true", validate_unregistered_source_finding(valid_finding(operator_review_required=False)))

    def test_20_empty_recommended_action_fails(self):
        self.assertIn("empty recommended_action", validate_unregistered_source_finding(valid_finding(recommended_action="")))

    def test_21_unregistered_voice_proactive_requires_operator_review(self):
        errors = validate_unregistered_source_finding(valid_finding(finding_type="unregistered_voice_or_proactive_source", operator_review_required=False))
        self.assertIn("operator_review_required must remain true", errors)
        self.assertIn("unregistered voice/proactive finding requires operator review", errors)

    def test_22_unregistered_self_improvement_requires_operator_review(self):
        errors = validate_unregistered_source_finding(valid_finding(finding_type="unregistered_self_improvement_source", operator_review_required=False))
        self.assertIn("operator_review_required must remain true", errors)
        self.assertIn("unregistered self-improvement finding requires operator review", errors)

    def assert_safety_flag_fails(self, field: str, expected: str):
        flags = UnregisteredSourceDetectionSafetyFlags(**{field: True})
        self.assertIn(expected, validate_unregistered_source_finding(valid_finding(safety_flags=flags)))

    def test_23_auto_registration_safety_flag_fails(self):
        self.assert_safety_flag_fails("auto_registration_attempted", "auto registration attempted")

    def test_24_auto_activation_safety_flag_fails(self):
        self.assert_safety_flag_fails("auto_activation_attempted", "auto activation attempted")

    def test_25_queue_write_safety_flag_fails(self):
        self.assert_safety_flag_fails("queue_write_attempted", "queue write attempted")

    def test_26_registry_persistence_safety_flag_fails(self):
        self.assert_safety_flag_fails("registry_persistence_attempted", "registry persistence attempted")

    def test_27_runtime_wiring_safety_flag_fails(self):
        self.assert_safety_flag_fails("runtime_wiring_attempted", "runtime wiring attempted")

    def test_28_memory_mutation_safety_flag_fails(self):
        self.assert_safety_flag_fails("memory_mutation_attempted", "memory mutation attempted")

    def test_29_external_model_call_safety_flag_fails(self):
        self.assert_safety_flag_fails("external_model_call_attempted", "external model call attempted")

    def test_30_advisor_call_safety_flag_fails(self):
        self.assert_safety_flag_fails("advisor_call_attempted", "advisor call attempted")

    def test_31_self_improvement_activation_safety_flag_fails(self):
        self.assert_safety_flag_fails("self_improvement_activation_attempted", "self-improvement activation attempted")

    def test_32_provenance_guessing_safety_flag_fails(self):
        self.assert_safety_flag_fails("provenance_guessing_attempted", "provenance guessing attempted")

    def test_33_answer_selection_safety_flag_fails(self):
        self.assert_safety_flag_fails("answer_selection_attempted", "answer selection attempted")

    def test_34_truth_authority_safety_flag_fails(self):
        self.assert_safety_flag_fails("truth_authority_claimed", "truth authority claimed")

    def test_35_soundness_authority_safety_flag_fails(self):
        self.assert_safety_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_36_official_score_safety_flag_fails(self):
        self.assert_safety_flag_fails("official_score_claimed", "official score claimed")

    def test_37_raw_sensitive_content_stored_safety_flag_fails(self):
        self.assert_safety_flag_fails("raw_sensitive_content_stored", "raw sensitive content stored")

    def test_38_missing_report_id_fails(self):
        self.assertIn("missing report_id", validate_unregistered_source_detection_report(valid_report(report_id="")))

    def test_39_report_finding_count_mismatch_fails(self):
        self.assertIn("finding_count mismatch", validate_unregistered_source_detection_report(valid_report(finding_count=99)))

    def test_40_report_auto_registration_performed_fails(self):
        self.assertIn("auto_registration_performed must remain false", validate_unregistered_source_detection_report(valid_report(auto_registration_performed=True)))

    def test_41_report_queue_writes_performed_fails(self):
        self.assertIn("queue_writes_performed must remain false", validate_unregistered_source_detection_report(valid_report(queue_writes_performed=True)))

    def test_42_report_runtime_changes_performed_fails(self):
        self.assertIn("runtime_changes_performed must remain false", validate_unregistered_source_detection_report(valid_report(runtime_changes_performed=True)))

    def test_43_report_external_model_calls_performed_fails(self):
        self.assertIn("external_model_calls_performed must remain false", validate_unregistered_source_detection_report(valid_report(external_model_calls_performed=True)))

    def test_44_finding_to_from_dict_roundtrip_works(self):
        item = valid_finding()
        restored = unregistered_source_finding_from_dict(unregistered_source_finding_to_dict(item))
        self.assertEqual(item, restored)

    def test_45_report_to_from_dict_roundtrip_works(self):
        item = valid_report()
        restored = unregistered_source_detection_report_from_dict(unregistered_source_detection_report_to_dict(item))
        self.assertEqual(item, restored)

    def test_46_single_finding_summary_is_redacted(self):
        item = valid_finding(evidence_summary="api key should be redacted")
        summary = summarize_unregistered_source_finding(item)
        rendered = json.dumps(summary, sort_keys=True).lower()
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertNotIn("api key should be redacted", rendered)

    def test_47_report_summary_is_redacted_count_only(self):
        report = valid_report(summary="token should be redacted")
        summary = summarize_unregistered_source_detection_report(report)
        rendered = json.dumps(summary, sort_keys=True).lower()
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertNotIn("token should be redacted", rendered)
        self.assertEqual(1, summary["finding_count"])

    def test_48_summary_avoids_sensitive_markers(self):
        summary = summarize_unregistered_source_detection_report(valid_report())
        rendered = json.dumps(summary, sort_keys=True).lower()
        for marker in PROHIBITED_SUMMARY_MARKERS:
            self.assertNotIn(marker, rendered)

    def test_49_design_test_still_passes_when_tree_clean_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_unregistered_source_detection_design_v1.py").exists())

    def test_50_provenance_source_registry_seed_tests_still_pass_when_tree_clean_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_provenance_source_registry_initial_seed_v1.py").exists())

    def test_51_provenance_source_registry_schema_tests_still_pass_when_tree_clean_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_provenance_source_registry_schema_v1.py").exists())

    def test_52_release_gate_check_available(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "release_gate_v1.py").exists())
        self.assertTrue((ROOT / "scripts" / "weslr_release_check.sh").exists())

    def test_53_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_54_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_55_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
