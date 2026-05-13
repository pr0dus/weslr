from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.local_scan_advisor_review import (  # noqa: E402
    ALLOWED_ADVISOR_CALL_MODES,
    ALLOWED_FINDING_TYPES,
    ALLOWED_RISK_LEVELS,
    ALLOWED_SCAN_MODES,
    LocalScanFinding,
    LocalScanReport,
    LocalScanSafetyFlags,
    create_empty_local_scan_finding,
    create_empty_local_scan_report,
    local_scan_finding_from_dict,
    local_scan_finding_to_dict,
    local_scan_report_from_dict,
    local_scan_report_to_dict,
    map_local_scan_finding_to_advisor_queue_item,
    summarize_local_scan_finding,
    summarize_local_scan_report,
    validate_local_scan_finding,
    validate_local_scan_report,
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
    )
    for key, value in overrides.items():
        setattr(finding, key, value)
    return finding


def valid_report(**overrides):
    report = create_empty_local_scan_report(
        scan_id="scan_001",
        trigger_reason="manual schema validation",
        summary="local scan report summary",
        findings=[valid_finding()],
    )
    for key, value in overrides.items():
        setattr(report, key, value)
    return report


class LocalScanAdvisorReviewSchemaV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(LocalScanSafetyFlags)
        self.assertTrue(LocalScanFinding)
        self.assertTrue(LocalScanReport)

    def test_02_empty_finding_instantiates(self):
        finding = LocalScanFinding()
        self.assertEqual("1.0", finding.schema_version)
        self.assertIsInstance(finding.safety_flags, LocalScanSafetyFlags)

    def test_03_empty_report_instantiates(self):
        report = LocalScanReport()
        self.assertEqual("1.0", report.schema_version)
        self.assertEqual([], report.findings)
        self.assertIsInstance(report.safety_flags, LocalScanSafetyFlags)

    def test_04_safe_defaults(self):
        finding = create_empty_local_scan_finding()
        report = create_empty_local_scan_report()
        self.assertTrue(finding.requires_operator_approval)
        self.assertEqual("local_scan_only", finding.advisor_call_mode)
        self.assertFalse(finding.advisor_call_allowed)
        self.assertFalse(report.would_create_queue_items)
        self.assertFalse(report.external_model_calls_made)
        self.assertFalse(report.runtime_changes_made)
        self.assertEqual("local_scan_only", report.scan_mode)

    def test_05_all_finding_types_validate(self):
        for value in ALLOWED_FINDING_TYPES:
            self.assertNotIn("invalid finding_type", validate_local_scan_finding(valid_finding(finding_type=value)))

    def test_06_invalid_finding_type_fails(self):
        self.assertIn("invalid finding_type", validate_local_scan_finding(valid_finding(finding_type="bad")))

    def test_07_all_risk_levels_validate(self):
        for value in ALLOWED_RISK_LEVELS:
            self.assertNotIn("invalid risk_level", validate_local_scan_finding(valid_finding(risk_level=value)))

    def test_08_invalid_risk_level_fails(self):
        self.assertIn("invalid risk_level", validate_local_scan_finding(valid_finding(risk_level="bad")))

    def test_09_all_advisor_call_modes_validate(self):
        for value in ALLOWED_ADVISOR_CALL_MODES:
            finding = valid_finding(advisor_call_mode=value)
            if value != "local_scan_only":
                finding.advisor_call_allowed = True
            self.assertNotIn("invalid advisor_call_mode", validate_local_scan_finding(finding))

    def test_10_invalid_advisor_call_mode_fails(self):
        self.assertIn("invalid advisor_call_mode", validate_local_scan_finding(valid_finding(advisor_call_mode="bad")))

    def test_11_all_scan_modes_validate(self):
        for value in ALLOWED_SCAN_MODES:
            self.assertNotIn("invalid scan_mode", validate_local_scan_report(valid_report(scan_mode=value)))

    def test_12_invalid_scan_mode_fails(self):
        self.assertIn("invalid scan_mode", validate_local_scan_report(valid_report(scan_mode="bad")))

    def test_13_missing_finding_id_fails(self):
        self.assertIn("missing finding_id", validate_local_scan_finding(valid_finding(finding_id="")))

    def test_14_missing_recommended_action_fails(self):
        self.assertIn("missing recommended_action", validate_local_scan_finding(valid_finding(recommended_action="")))

    def test_15_requires_operator_approval_false_fails(self):
        self.assertIn("requires_operator_approval must remain true", validate_local_scan_finding(valid_finding(requires_operator_approval=False)))

    def test_16_advisor_call_allowed_true_with_local_scan_only_fails(self):
        self.assertIn(
            "advisor_call_allowed true is incompatible with local_scan_only",
            validate_local_scan_finding(valid_finding(advisor_call_allowed=True, advisor_call_mode="local_scan_only")),
        )

    def assert_flag_fails(self, field: str, expected: str):
        flags = LocalScanSafetyFlags(**{field: True})
        self.assertIn(expected, validate_local_scan_finding(valid_finding(safety_flags=flags)))
        self.assertIn(expected, validate_local_scan_report(valid_report(safety_flags=flags)))

    def test_17_external_model_call_attempted_fails(self):
        self.assert_flag_fails("external_model_call_attempted", "external model call attempted")

    def test_18_advisor_call_attempted_fails(self):
        self.assert_flag_fails("advisor_call_attempted", "advisor call attempted")

    def test_19_queue_item_created_flag_fails(self):
        self.assert_flag_fails("queue_item_created", "queue item created")

    def test_20_prompt_mutation_requested_fails(self):
        self.assert_flag_fails("prompt_mutation_requested", "prompt mutation requested")

    def test_21_provider_activation_requested_fails(self):
        self.assert_flag_fails("provider_activation_requested", "provider activation requested")

    def test_22_runtime_config_change_requested_fails(self):
        self.assert_flag_fails("runtime_config_change_requested", "runtime/config change requested")

    def test_23_memory_mutation_requested_fails(self):
        self.assert_flag_fails("memory_mutation_requested", "memory mutation requested")

    def test_24_governance_override_requested_fails(self):
        self.assert_flag_fails("governance_override_requested", "governance override requested")

    def test_25_answer_selection_requested_fails(self):
        self.assert_flag_fails("answer_selection_requested", "answer selection requested")

    def test_26_truth_authority_requested_fails(self):
        self.assert_flag_fails("truth_authority_requested", "truth authority requested")

    def test_27_soundness_authority_requested_fails(self):
        self.assert_flag_fails("soundness_authority_requested", "soundness authority requested")

    def test_28_official_score_requested_fails(self):
        self.assert_flag_fails("official_score_requested", "official score requested")

    def test_29_answer_key_requested_fails(self):
        self.assert_flag_fails("answer_key_requested", "answer key requested")

    def test_30_raw_benchmark_text_requested_fails(self):
        self.assert_flag_fails("raw_benchmark_text_requested", "raw benchmark text requested")

    def test_31_secrets_requested_fails(self):
        self.assert_flag_fails("secrets_requested", "secrets requested")

    def test_32_missing_scan_id_fails(self):
        self.assertIn("missing scan_id", validate_local_scan_report(valid_report(scan_id="")))

    def test_33_would_create_queue_items_true_fails(self):
        self.assertIn("would_create_queue_items must remain false", validate_local_scan_report(valid_report(would_create_queue_items=True)))

    def test_34_external_model_calls_made_true_fails(self):
        self.assertIn("external_model_calls_made must remain false", validate_local_scan_report(valid_report(external_model_calls_made=True)))

    def test_35_runtime_changes_made_true_fails(self):
        self.assertIn("runtime_changes_made must remain false", validate_local_scan_report(valid_report(runtime_changes_made=True)))

    def test_36_finding_to_from_dict_roundtrip_works(self):
        finding = valid_finding(affected_templates=["template_v1"], notes=["operator-visible metadata"])
        self.assertEqual(finding, local_scan_finding_from_dict(local_scan_finding_to_dict(finding)))

    def test_37_report_to_from_dict_roundtrip_works(self):
        report = valid_report(findings=[valid_finding(affected_providers=["provider_1"])])
        self.assertEqual(report, local_scan_report_from_dict(local_scan_report_to_dict(report)))

    def test_38_single_finding_summary_is_redacted(self):
        finding = valid_finding(
            finding_id="finding_api_key_token_secret",
            trigger_reason="api key token secret raw benchmark text answer key private user data",
            evidence_summary="Bearer abc.def official score password:=x",
        )
        rendered = json.dumps(summarize_local_scan_finding(finding)).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data", "bearer abc.def", "official score", "password"]:
            self.assertNotIn(forbidden, rendered)

    def test_39_report_summary_is_redacted_count_only(self):
        report = valid_report(
            scan_id="scan_api_key_token_secret",
            summary="raw benchmark text answer key private user data",
            findings=[valid_finding(finding_type="review_due"), valid_finding(finding_type="provider_health_note", risk_level="medium")],
        )
        summary = summarize_local_scan_report(report)
        rendered = json.dumps(summary).lower()
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(2, summary["finding_count"])
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_40_summary_does_not_contain_sensitive_strings(self):
        report = valid_report(
            scan_id="scan_001",
            trigger_reason="call model activate provider edit prompt update config write memory override governance select answer prove true official score",
            summary="sk-abc123 token secret raw benchmark answer key private user data",
        )
        rendered = json.dumps(summarize_local_scan_report(report)).lower()
        for forbidden in ["sk-abc123", "token", "secret", "raw benchmark", "answer key", "private user data", "call model", "activate provider", "edit prompt", "official score"]:
            self.assertNotIn(forbidden, rendered)

    def test_41_local_scan_adapter_design_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_local_scan_only_advisor_review_adapter_design_v1.py"], cwd=str(ROOT), check=True)

    def test_42_mapping_helper_import_smoke_test(self):
        self.assertIsNotNone(map_local_scan_finding_to_advisor_queue_item)

    def test_43_advisor_review_queue_schema_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_schema_v1.py"], cwd=str(ROOT), check=True)

    def test_44_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_45_no_forbidden_files_changed(self):
        changed = set(subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines())
        staged = set(subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines())
        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines())
        all_changed = changed | staged | untracked
        self.assertFalse(all_changed & FORBIDDEN_CHANGED)
        self.assertFalse(all_changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(all_changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
