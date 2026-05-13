from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue import validate_advisor_review_queue_item  # noqa: E402
from weslr.local_scan_advisor_review import (  # noqa: E402
    LocalScanFinding,
    LocalScanReport,
    LocalScanSafetyFlags,
    create_empty_local_scan_finding,
    create_empty_local_scan_report,
    map_local_scan_finding_to_advisor_queue_item,
    map_local_scan_report_to_advisor_queue_items,
    summarize_local_scan_queue_mapping_diagnostics,
)

ALLOWED_CHANGED = {
    "weslr/local_scan_advisor_review.py",
    "weslr/tests/test_local_scan_advisor_review_schema_v1.py",
    "weslr/tests/test_local_scan_advisor_queue_mapping_helpers_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_discovery/review.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_finding(**overrides):
    finding = create_empty_local_scan_finding(
        finding_id="finding_001",
        trigger_reason="prompt template review metadata is stale",
        recommended_action="operator review of advisor prompt coverage",
        finding_type="stale_prompt_template",
        notes=["operator-visible local note"],
    )
    for key, value in overrides.items():
        setattr(finding, key, value)
    return finding


def valid_report(**overrides):
    report = create_empty_local_scan_report(
        scan_id="scan_001",
        trigger_reason="manual schema validation",
        summary="local scan report summary",
        findings=[valid_finding(), valid_finding(finding_id="finding_002", finding_type="provider_health_note")],
    )
    for key, value in overrides.items():
        setattr(report, key, value)
    return report


class LocalScanAdvisorQueueMappingHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(map_local_scan_finding_to_advisor_queue_item)
        self.assertTrue(map_local_scan_report_to_advisor_queue_items)
        self.assertTrue(summarize_local_scan_queue_mapping_diagnostics)

    def test_02_valid_finding_maps_to_queue_item_proposal(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertEqual([], result["validation_errors"])
        self.assertIsNotNone(result["queue_item"])

    def test_03_mapped_queue_item_validates(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding())["queue_item"]
        self.assertEqual([], validate_advisor_review_queue_item(item))

    def test_04_finding_type_maps_to_expected_suggestion_type(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="missing_template_coverage"))["queue_item"]
        self.assertEqual("prompt_template_review", item.suggestion_type)

    def test_05_stale_prompt_template_maps_to_prompt_template_review(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="stale_prompt_template"))["queue_item"]
        self.assertEqual("prompt_template_review", item.suggestion_type)

    def test_06_provider_health_note_maps_to_provider_registry_review(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="provider_health_note"))["queue_item"]
        self.assertEqual("provider_registry_review", item.suggestion_type)

    def test_07_capability_scope_gap_maps_to_capability_scope_review(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="capability_scope_gap"))["queue_item"]
        self.assertEqual("capability_scope_review", item.suggestion_type)

    def test_08_unsupported_gap_trend_maps_to_gap_taxonomy_review(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="unsupported_gap_trend"))["queue_item"]
        self.assertEqual("gap_taxonomy_review", item.suggestion_type)

    def test_09_unknown_finding_maps_conservatively(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(finding_type="unknown", risk_level="medium"))["queue_item"]
        self.assertEqual("advisor_review", item.suggestion_type)
        self.assertEqual("unknown", item.risk_level)
        self.assertTrue(any("mapped conservatively" in note for note in item.notes))

    def test_10_requires_operator_approval_remains_true(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding())["queue_item"]
        self.assertTrue(item.requires_operator_approval)

    def test_11_advisor_call_allowed_remains_false(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(advisor_call_mode="disabled", advisor_call_allowed=True))["queue_item"]
        self.assertFalse(item.advisor_call_allowed)

    def test_12_advisor_call_mode_remains_local_scan_only(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding(advisor_call_mode="disabled", advisor_call_allowed=True))["queue_item"]
        self.assertEqual("local_scan_only", item.advisor_call_mode)

    def test_13_source_is_local_scan(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding())["queue_item"]
        self.assertEqual("local_scan", item.source)

    def test_14_review_status_pending(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding())["queue_item"]
        self.assertEqual("pending_review", item.review_status)

    def test_15_operator_decision_pending(self):
        item = map_local_scan_finding_to_advisor_queue_item(valid_finding())["queue_item"]
        self.assertEqual("pending_review", item.operator_decision)

    def test_16_invalid_finding_produces_validation_error_and_no_trusted_proposal(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding(recommended_action=""))
        self.assertIsNone(result["queue_item"])
        self.assertTrue(result["validation_errors"])

    def test_17_report_maps_multiple_findings(self):
        result = map_local_scan_report_to_advisor_queue_items(valid_report())
        self.assertEqual(2, len(result["queue_items"]))
        self.assertEqual([], result["validation_errors"])

    def test_18_invalid_report_fails_safely(self):
        result = map_local_scan_report_to_advisor_queue_items(valid_report(scan_id="", findings=[valid_finding(recommended_action="")]))
        self.assertTrue(result["validation_errors"])
        self.assertEqual([], result["queue_items"])

    def test_19_no_persistence_performed(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["persisted"])

    def test_20_no_queue_files_written(self):
        with patch("builtins.open", side_effect=AssertionError("unexpected file write")), patch("pathlib.Path.write_text", side_effect=AssertionError("unexpected Path.write_text")), patch("pathlib.Path.write_bytes", side_effect=AssertionError("unexpected Path.write_bytes")):
            result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertIsNotNone(result["queue_item"])

    def test_21_no_external_model_calls(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["external_model_calls_made"])

    def test_22_no_runtime_config_changes(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["runtime_changes_made"])

    def test_23_no_answer_selection(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["answer_selection"])

    def test_24_no_truth_soundness_claim(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["truth_claim"])

    def test_25_no_official_score(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding())
        self.assertFalse(result["official_score"])

    def test_26_summary_is_redacted_count_only(self):
        summary = summarize_local_scan_queue_mapping_diagnostics(valid_report())
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(2, summary["finding_count"])
        self.assertEqual(2, summary["mapped_queue_item_proposal_count"])

    def test_27_summary_does_not_contain_sensitive_strings(self):
        report = valid_report(findings=[valid_finding(trigger_reason="api key token secret", evidence_summary="answer key raw benchmark text private user data")])
        summary = summarize_local_scan_queue_mapping_diagnostics(report)
        rendered = json.dumps(summary).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_28_high_risk_requires_notes_to_validate(self):
        result = map_local_scan_finding_to_advisor_queue_item(valid_finding(risk_level="high", notes=[]))
        self.assertIsNone(result["queue_item"])
        self.assertTrue(any("high risk item requires notes" in err for err in result["validation_errors"]))

    def test_29_dict_input_maps_without_mutating_source(self):
        finding_dict = {
            "finding_id": "finding_dict_001",
            "finding_type": "review_due",
            "trigger_reason": "manual review is due",
            "recommended_action": "queue for operator review",
            "notes": ["safe note"],
        }
        original = json.loads(json.dumps(finding_dict))
        result = map_local_scan_finding_to_advisor_queue_item(finding_dict)
        self.assertIsNotNone(result["queue_item"])
        self.assertEqual(original, finding_dict)

    def test_30_report_diagnostics_count_validation_errors(self):
        result = map_local_scan_report_to_advisor_queue_items(valid_report(findings=[valid_finding(recommended_action="")]))
        summary = summarize_local_scan_queue_mapping_diagnostics(result)
        self.assertEqual(1, summary["finding_count"])
        self.assertGreaterEqual(summary["validation_error_count"], 1)

    def test_31_design_test_file_exists_for_clean_tree_validation(self):
        self.assertTrue((ROOT / "weslr" / "tests" / "test_local_scan_advisor_queue_mapping_helpers_design_v1.py").exists())

    def test_32_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
