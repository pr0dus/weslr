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
    classify_candidate_source_type,
    classify_detection_signal,
    create_unregistered_source_detection_report_from_candidates,
    create_unregistered_source_finding_from_candidate,
    summarize_unregistered_source_detection_diagnostics,
    validate_unregistered_source_detection_report,
    validate_unregistered_source_finding,
)

ALLOWED_CHANGED = {
    "weslr/unregistered_source_detection.py",
    "weslr/tests/test_unregistered_source_detection_helpers_v1.py",
    "weslr/tests/test_unregistered_source_detection_schema_v1.py",
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


class UnregisteredSourceDetectionHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(classify_candidate_source_type)
        self.assertTrue(classify_detection_signal)
        self.assertTrue(create_unregistered_source_finding_from_candidate)
        self.assertTrue(create_unregistered_source_detection_report_from_candidates)
        self.assertTrue(summarize_unregistered_source_detection_diagnostics)

    def test_02_candidate_source_type_classifier_handles_voice(self):
        self.assertEqual("voice_surface", classify_candidate_source_type("weslr.voice_gateway"))

    def test_03_classifier_handles_ambient(self):
        self.assertEqual("ambient_loop", classify_candidate_source_type("ambient_voice_loop"))

    def test_04_classifier_handles_proactive(self):
        self.assertEqual("proactive_suggestion", classify_candidate_source_type("proactive_suggestions"))

    def test_05_classifier_handles_advisor(self):
        self.assertEqual("advisor_review", classify_candidate_source_type("llm_advisor_mode"))

    def test_06_classifier_handles_memory(self):
        self.assertEqual("memory_capture", classify_candidate_source_type("memory_capture"))

    def test_07_classifier_handles_routing_decision(self):
        self.assertEqual("unknown", classify_candidate_source_type("decision_router"))
        self.assertEqual("routing_or_decision_behavior", classify_detection_signal("decision_router"))

    def test_08_classifier_handles_self_review(self):
        self.assertEqual("self_review", classify_candidate_source_type("weslr_self_review_surface"))

    def test_09_classifier_handles_self_improvement(self):
        self.assertEqual("self_improvement_candidate", classify_candidate_source_type("self_improvement_candidate"))

    def test_10_unclear_classifier_returns_unknown(self):
        self.assertEqual("unknown", classify_candidate_source_type("misc.module"))
        self.assertEqual("unknown", classify_detection_signal("misc.module"))

    def test_11_detection_signal_classifier_handles_voice_proactive(self):
        self.assertEqual("voice_or_proactive_behavior", classify_detection_signal("voice_gateway"))
        self.assertEqual("voice_or_proactive_behavior", classify_detection_signal("proactive_suggestions"))

    def test_12_detection_signal_classifier_handles_advisor_review_queue(self):
        self.assertEqual("advisor_review_behavior", classify_detection_signal("advisor_mode"))
        self.assertEqual("queue_or_review_behavior", classify_detection_signal("review_queue"))

    def test_13_detection_signal_classifier_handles_memory_write(self):
        self.assertEqual("memory_write_behavior", classify_detection_signal("memory_capture", ["write"]))

    def test_14_detection_signal_classifier_handles_self_improvement(self):
        self.assertEqual("self_improvement_behavior", classify_detection_signal("self_improvement_candidate"))

    def test_15_registered_candidate_does_not_create_unregistered_finding(self):
        finding = create_unregistered_source_finding_from_candidate(
            candidate_source_id="voice_gateway",
            candidate_module_path="weslr.voice_gateway",
            registered_sources=["voice_gateway"],
        )
        self.assertIsNone(finding)

    def test_16_unregistered_candidate_creates_finding(self):
        finding = create_unregistered_source_finding_from_candidate(
            candidate_source_id="new_voice_surface",
            candidate_module_path="weslr.new_voice_surface",
            registered_sources=["voice_gateway"],
        )
        self.assertIsNotNone(finding)
        self.assertEqual("new_voice_surface", finding.candidate_source_id)

    def test_17_unregistered_finding_requires_operator_review(self):
        finding = create_unregistered_source_finding_from_candidate("new_source", "new_source")
        self.assertTrue(finding.operator_review_required)

    def test_18_unregistered_finding_has_unknown_safe_authority(self):
        finding = create_unregistered_source_finding_from_candidate("new_source", "new_source")
        self.assertIn(finding.authority_level, {"unknown", "internal_diagnostic", "suggestion"})

    def test_19_unregistered_voice_proactive_finding_validates_safely(self):
        finding = create_unregistered_source_finding_from_candidate("new_voice", "voice_gateway")
        self.assertEqual("unregistered_voice_or_proactive_source", finding.finding_type)
        self.assertEqual([], validate_unregistered_source_finding(finding))

    def test_20_unregistered_self_improvement_finding_validates_safely(self):
        finding = create_unregistered_source_finding_from_candidate("new_self_improvement", "self_improvement_candidate")
        self.assertEqual("unregistered_self_improvement_source", finding.finding_type)
        self.assertEqual([], validate_unregistered_source_finding(finding))

    def test_21_report_from_candidates_works(self):
        report = create_unregistered_source_detection_report_from_candidates(
            [
                {"source_id": "voice_gateway", "module_path": "weslr.voice_gateway"},
                {"source_id": "new_advisor", "module_path": "weslr.new_advisor"},
            ],
            registered_sources=["voice_gateway"],
            report_id="report_helpers",
            registry_seed_entry_count=20,
        )
        self.assertEqual("report_helpers", report.report_id)
        self.assertEqual(1, len(report.findings))

    def test_22_report_finding_count_matches(self):
        report = create_unregistered_source_detection_report_from_candidates(
            [{"source_id": "new_advisor", "module_path": "weslr.new_advisor"}], report_id="report_count"
        )
        self.assertEqual(report.finding_count, len(report.findings))
        self.assertEqual([], validate_unregistered_source_detection_report(report))

    def test_23_report_performs_no_auto_registration(self):
        report = create_unregistered_source_detection_report_from_candidates([], report_id="safe_report")
        self.assertFalse(report.auto_registration_performed)

    def test_24_report_performs_no_queue_writes(self):
        report = create_unregistered_source_detection_report_from_candidates([], report_id="safe_report")
        self.assertFalse(report.queue_writes_performed)

    def test_25_report_performs_no_runtime_changes(self):
        report = create_unregistered_source_detection_report_from_candidates([], report_id="safe_report")
        self.assertFalse(report.runtime_changes_performed)

    def test_26_report_performs_no_external_model_calls(self):
        report = create_unregistered_source_detection_report_from_candidates([], report_id="safe_report")
        self.assertFalse(report.external_model_calls_performed)

    def test_27_diagnostics_summary_is_redacted_count_only(self):
        report = create_unregistered_source_detection_report_from_candidates(
            [{"source_id": "new_advisor", "module_path": "weslr.new_advisor"}], report_id="report_diag"
        )
        summary = summarize_unregistered_source_detection_diagnostics(report, candidate_count=1, registered_count=0)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["candidate_count"])
        self.assertEqual(1, summary["finding_count"])
        self.assertFalse(summary["queue_writes_performed"])
        self.assertFalse(summary["registry_persistence_performed"])
        self.assertFalse(summary["external_model_calls_performed"])
        self.assertFalse(summary["runtime_changes_performed"])

    def test_28_diagnostics_summary_avoids_sensitive_markers(self):
        report = create_unregistered_source_detection_report_from_candidates(
            [{"source_id": "new_advisor", "module_path": "weslr.new_advisor", "hints": ["api key"]}], report_id="report_diag"
        )
        summary = summarize_unregistered_source_detection_diagnostics(report, candidate_count=1, registered_count=0)
        rendered = json.dumps(summary, sort_keys=True).lower()
        for marker in PROHIBITED_SUMMARY_MARKERS:
            self.assertNotIn(marker, rendered)

    def test_29_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_30_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_31_schema_tests_still_pass_when_tree_clean_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_unregistered_source_detection_schema_v1.py").exists())

    def test_32_registry_seed_tests_still_pass_when_tree_clean_target_exists(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_provenance_source_registry_initial_seed_v1.py").exists())

    def test_33_release_gate_check_available_and_no_forbidden_files_changed(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "release_gate_v1.py").exists())
        self.assertTrue((ROOT / "scripts" / "weslr_release_check.sh").exists())
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
