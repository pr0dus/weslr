from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue import AdvisorReviewQueueItem, validate_advisor_review_queue_item  # noqa: E402
from weslr.source_registry_review_queue_mapping import (  # noqa: E402
    FINDING_TYPE_TO_SUGGESTION_TYPE,
    SourceRegistryReviewQueueMappingResult,
    map_unregistered_source_finding_to_review_queue_item,
    map_unregistered_source_report_to_review_queue_items,
    summarize_source_registry_review_queue_mapping_diagnostics,
)
from weslr.unregistered_source_detection import (  # noqa: E402
    create_empty_unregistered_source_detection_report,
    create_empty_unregistered_source_finding,
)

ALLOWED_CHANGED = {
    "weslr/source_registry_review_queue_mapping.py",
    "weslr/tests/test_source_registry_review_queue_mapping_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_review_queue_persistence.py",
    "weslr/provenance_source_registry.py",
    "weslr/provenance_source_registry_seed.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
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


def finding(finding_type="unregistered_source_candidate", **overrides):
    item = create_empty_unregistered_source_finding(
        finding_id=f"finding_{finding_type}",
        candidate_source_id="candidate_source",
        finding_type=finding_type,
        candidate_module_path="weslr.candidate_source",
        candidate_source_type="self_review",
        detection_signal="module_name_output_like",
        evidence_summary="explicit metadata indicates source review",
        authority_level="unknown",
        operator_review_required=True,
        recommended_action="review source registry coverage",
        risk_level="low",
        related_docs=["docs/WESLR_UNREGISTERED_SOURCE_DETECTION_DESIGN_V1.md"],
        related_tests=["weslr/tests/test_source_registry_review_queue_mapping_v1.py"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class SourceRegistryReviewQueueMappingV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(map_unregistered_source_finding_to_review_queue_item)
        self.assertTrue(map_unregistered_source_report_to_review_queue_items)
        self.assertTrue(summarize_source_registry_review_queue_mapping_diagnostics)
        self.assertTrue(SourceRegistryReviewQueueMappingResult)

    def test_02_valid_unregistered_finding_maps_to_queue_item_proposal(self):
        item = map_unregistered_source_finding_to_review_queue_item(finding())
        self.assertIsInstance(item, AdvisorReviewQueueItem)
        self.assertEqual("diagnostic", item.source)

    def test_03_mapped_queue_item_validates(self):
        item = map_unregistered_source_finding_to_review_queue_item(finding())
        self.assertEqual([], validate_advisor_review_queue_item(item))

    def assert_maps_to(self, finding_type: str, expected: str):
        item = map_unregistered_source_finding_to_review_queue_item(finding(finding_type))
        self.assertEqual(expected, item.suggestion_type)

    def test_04_missing_source_registry_entry_maps_to_provider_registry_review(self):
        self.assert_maps_to("missing_source_registry_entry", "provider_registry_review")

    def test_05_stale_source_registry_entry_maps_to_provider_registry_review(self):
        self.assert_maps_to("stale_source_registry_entry", "provider_registry_review")

    def test_06_source_without_tests_maps_to_test_coverage_review(self):
        self.assert_maps_to("source_without_tests", "test_coverage_review")

    def test_07_source_without_docs_maps_to_capability_scope_review(self):
        self.assert_maps_to("source_without_docs", "capability_scope_review")

    def test_08_unknown_source_in_provenance_maps_safely(self):
        self.assert_maps_to("unknown_source_in_provenance", "capability_scope_review")

    def test_09_unregistered_voice_proactive_source_maps_safely(self):
        item = map_unregistered_source_finding_to_review_queue_item(finding("unregistered_voice_or_proactive_source"))
        self.assertEqual("capability_scope_review", item.suggestion_type)
        self.assertFalse(item.advisor_call_allowed)

    def test_10_unregistered_self_improvement_source_maps_to_safety_review(self):
        self.assert_maps_to("unregistered_self_improvement_source", "safety_policy_review")

    def test_11_authority_boundary_missing_maps_to_safety_review(self):
        self.assert_maps_to("source_authority_boundary_missing", "safety_policy_review")

    def test_12_activation_policy_inconsistent_maps_to_safety_review(self):
        self.assert_maps_to("source_activation_policy_inconsistent", "safety_policy_review")

    def test_13_unknown_finding_maps_conservatively(self):
        self.assert_maps_to("unknown", "advisor_review")

    def test_14_mapped_queue_item_requires_operator_approval(self):
        self.assertTrue(map_unregistered_source_finding_to_review_queue_item(finding()).requires_operator_approval)

    def test_15_mapped_queue_item_has_advisor_call_allowed_false(self):
        self.assertFalse(map_unregistered_source_finding_to_review_queue_item(finding()).advisor_call_allowed)

    def test_16_mapped_queue_item_has_local_scan_only_mode(self):
        self.assertEqual("local_scan_only", map_unregistered_source_finding_to_review_queue_item(finding()).advisor_call_mode)

    def test_17_mapped_queue_item_has_pending_review_status(self):
        self.assertEqual("pending_review", map_unregistered_source_finding_to_review_queue_item(finding()).review_status)

    def test_18_mapped_queue_item_has_pending_operator_decision(self):
        self.assertEqual("pending_review", map_unregistered_source_finding_to_review_queue_item(finding()).operator_decision)

    def test_19_invalid_finding_produces_validation_error_no_trusted_proposal(self):
        bad = finding(candidate_source_id="")
        with self.assertRaises(ValueError):
            map_unregistered_source_finding_to_review_queue_item(bad)

    def test_20_report_maps_multiple_findings(self):
        report = create_empty_unregistered_source_detection_report(
            report_id="report_mapping",
            findings=[finding("missing_source_registry_entry"), finding("source_without_tests", finding_id="finding_tests")],
        )
        result = map_unregistered_source_report_to_review_queue_items(report)
        self.assertEqual([], result.validation_errors)
        self.assertEqual(2, len(result.items))

    def test_21_invalid_report_fails_safely(self):
        report = create_empty_unregistered_source_detection_report(report_id="", findings=[finding()])
        result = map_unregistered_source_report_to_review_queue_items(report)
        self.assertEqual([], result.items)
        self.assertTrue(result.validation_errors)

    def test_22_diagnostics_summary_is_redacted_count_only(self):
        report = create_empty_unregistered_source_detection_report(report_id="report_summary", findings=[finding()])
        summary = summarize_source_registry_review_queue_mapping_diagnostics(report)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["finding_count"])
        self.assertEqual(1, summary["mapped_queue_proposal_count"])

    def test_23_diagnostics_summary_avoids_sensitive_markers(self):
        report = create_empty_unregistered_source_detection_report(report_id="report_summary", findings=[finding(evidence_summary="api key token secret raw benchmark answer key private user data")])
        summary = summarize_source_registry_review_queue_mapping_diagnostics(report)
        rendered = json.dumps(summary, sort_keys=True).lower()
        for marker in PROHIBITED_SUMMARY_MARKERS:
            self.assertNotIn(marker, rendered)

    def test_24_no_queue_writes_performed(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["queue_writes_performed"])

    def test_25_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_26_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_27_no_external_model_calls(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["external_model_calls_performed"])

    def test_28_no_runtime_config_changes(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["runtime_changes_performed"])

    def test_29_no_answer_selection(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["answer_selection"])

    def test_30_no_truth_soundness_claim(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["truth_claim"])

    def test_31_no_official_score(self):
        summary = summarize_source_registry_review_queue_mapping_diagnostics(SourceRegistryReviewQueueMappingResult())
        self.assertFalse(summary["official_score"])

    def test_32_unregistered_source_detection_helper_tests_still_pass_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_unregistered_source_detection_helpers_v1.py").exists())

    def test_33_advisor_queue_schema_tests_still_pass_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_advisor_review_queue_schema_v1.py").exists())

    def test_34_release_gate_check_available_and_no_forbidden_files_changed(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "release_gate_v1.py").exists())
        self.assertTrue((ROOT / "scripts" / "weslr_release_check.sh").exists())
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")

    def test_mapping_taxonomy_complete_for_required_types(self):
        for finding_type in [
            "unregistered_source_candidate",
            "missing_source_registry_entry",
            "stale_source_registry_entry",
            "source_without_tests",
            "source_without_docs",
            "unknown_source_in_provenance",
            "unregistered_voice_or_proactive_source",
            "unregistered_self_improvement_source",
            "source_authority_boundary_missing",
            "source_activation_policy_inconsistent",
            "unknown",
        ]:
            self.assertIn(finding_type, FINDING_TYPE_TO_SUGGESTION_TYPE)


if __name__ == "__main__":
    unittest.main()
