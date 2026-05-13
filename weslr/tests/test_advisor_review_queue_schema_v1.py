from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue import (  # noqa: E402
    ALLOWED_ADVISOR_CALL_MODES,
    ALLOWED_OPERATOR_DECISIONS,
    ALLOWED_REVIEW_STATUSES,
    ALLOWED_RISK_LEVELS,
    ALLOWED_SOURCES,
    ALLOWED_SUGGESTION_TYPES,
    AdvisorReviewQueueItem,
    AdvisorReviewQueueSafetyFlags,
    advisor_review_queue_item_from_dict,
    advisor_review_queue_item_to_dict,
    create_empty_advisor_review_queue_item,
    summarize_advisor_review_queue_item,
    summarize_advisor_review_queue_items,
    validate_advisor_review_queue_item,
)

ALLOWED_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/tests/test_advisor_review_queue_schema_v1.py",
}
FORBIDDEN_CHANGED = {
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


def valid_item(**overrides):
    item = create_empty_advisor_review_queue_item(
        suggestion_id="sug_001",
        trigger_reason="prompt template lifecycle review due",
        recommended_action="review prompt template coverage",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class AdvisorReviewQueueSchemaV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(AdvisorReviewQueueItem)
        self.assertTrue(AdvisorReviewQueueSafetyFlags)

    def test_02_empty_queue_item_instantiates(self):
        item = AdvisorReviewQueueItem()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, AdvisorReviewQueueSafetyFlags)

    def test_03_safe_defaults_require_operator_approval(self):
        item = create_empty_advisor_review_queue_item()
        self.assertTrue(item.requires_operator_approval)
        self.assertFalse(item.advisor_call_allowed)

    def test_04_default_advisor_call_mode_is_local_scan_only(self):
        self.assertEqual("local_scan_only", create_empty_advisor_review_queue_item().advisor_call_mode)

    def test_05_all_suggestion_types_validate(self):
        for value in ALLOWED_SUGGESTION_TYPES:
            self.assertNotIn("invalid suggestion_type", validate_advisor_review_queue_item(valid_item(suggestion_type=value)))

    def test_06_invalid_suggestion_type_fails(self):
        self.assertIn("invalid suggestion_type", validate_advisor_review_queue_item(valid_item(suggestion_type="bad")))

    def test_07_all_sources_validate(self):
        for value in ALLOWED_SOURCES:
            self.assertNotIn("invalid source", validate_advisor_review_queue_item(valid_item(source=value)))

    def test_08_invalid_source_fails(self):
        self.assertIn("invalid source", validate_advisor_review_queue_item(valid_item(source="bad")))

    def test_09_all_risk_levels_validate(self):
        for value in ALLOWED_RISK_LEVELS:
            item = valid_item(risk_level=value)
            if value == "high":
                item.notes.append("high risk needs operator review")
            self.assertNotIn("invalid risk_level", validate_advisor_review_queue_item(item))

    def test_10_invalid_risk_level_fails(self):
        self.assertIn("invalid risk_level", validate_advisor_review_queue_item(valid_item(risk_level="bad")))

    def test_11_all_advisor_call_modes_validate(self):
        for value in ALLOWED_ADVISOR_CALL_MODES:
            item = valid_item(advisor_call_mode=value)
            self.assertNotIn("invalid advisor_call_mode", validate_advisor_review_queue_item(item))

    def test_12_invalid_advisor_call_mode_fails(self):
        self.assertIn("invalid advisor_call_mode", validate_advisor_review_queue_item(valid_item(advisor_call_mode="bad")))

    def test_13_all_review_statuses_validate(self):
        for value in ALLOWED_REVIEW_STATUSES:
            self.assertNotIn("invalid review_status", validate_advisor_review_queue_item(valid_item(review_status=value)))

    def test_14_invalid_review_status_fails(self):
        self.assertIn("invalid review_status", validate_advisor_review_queue_item(valid_item(review_status="bad")))

    def test_15_all_operator_decisions_validate(self):
        for value in ALLOWED_OPERATOR_DECISIONS:
            self.assertNotIn("invalid operator_decision", validate_advisor_review_queue_item(valid_item(operator_decision=value)))

    def test_16_invalid_operator_decision_fails(self):
        self.assertIn("invalid operator_decision", validate_advisor_review_queue_item(valid_item(operator_decision="bad")))

    def test_17_missing_suggestion_id_fails(self):
        self.assertIn("missing suggestion_id", validate_advisor_review_queue_item(valid_item(suggestion_id="")))

    def test_18_empty_recommended_action_fails(self):
        self.assertIn("empty recommended_action", validate_advisor_review_queue_item(valid_item(recommended_action="")))

    def test_19_requires_operator_approval_false_fails(self):
        self.assertIn("requires_operator_approval must remain true", validate_advisor_review_queue_item(valid_item(requires_operator_approval=False)))

    def test_20_advisor_call_allowed_true_with_local_scan_only_fails(self):
        self.assertIn(
            "advisor_call_allowed true is incompatible with local_scan_only",
            validate_advisor_review_queue_item(valid_item(advisor_call_allowed=True, advisor_call_mode="local_scan_only")),
        )

    def assert_flag_fails(self, field: str, expected: str):
        flags = AdvisorReviewQueueSafetyFlags(**{field: True})
        self.assertIn(expected, validate_advisor_review_queue_item(valid_item(safety_flags=flags)))

    def test_21_answer_selection_requested_fails(self):
        self.assert_flag_fails("answer_selection_requested", "answer selection requested")

    def test_22_truth_authority_requested_fails(self):
        self.assert_flag_fails("truth_authority_requested", "truth authority requested")

    def test_23_soundness_authority_requested_fails(self):
        self.assert_flag_fails("soundness_authority_requested", "soundness authority requested")

    def test_24_official_score_requested_fails(self):
        self.assert_flag_fails("official_score_requested", "official score requested")

    def test_25_answer_key_requested_fails(self):
        self.assert_flag_fails("answer_key_requested", "answer key requested")

    def test_26_benchmark_specific_tuning_requested_fails(self):
        self.assert_flag_fails("benchmark_specific_tuning_requested", "benchmark-specific tuning requested")

    def test_27_raw_benchmark_text_requested_fails(self):
        self.assert_flag_fails("raw_benchmark_text_requested", "raw benchmark text requested")

    def test_28_secrets_requested_fails(self):
        self.assert_flag_fails("secrets_requested", "secrets requested")

    def test_29_private_user_data_requested_fails(self):
        self.assert_flag_fails("private_user_data_requested", "private user data requested")

    def test_30_memory_mutation_requested_fails(self):
        self.assert_flag_fails("memory_mutation_requested", "memory mutation requested")

    def test_31_runtime_config_change_requested_fails(self):
        self.assert_flag_fails("runtime_config_change_requested", "runtime/config change requested")

    def test_32_governance_override_requested_fails(self):
        self.assert_flag_fails("governance_override_requested", "governance override requested")

    def test_33_automatic_external_model_call_flag_fails(self):
        self.assert_flag_fails("external_model_call_auto_allowed", "automatic external model call allowed")

    def test_34_to_from_dict_roundtrip_works(self):
        item = valid_item(affected_templates=["v1"], notes=["operator-visible note"])
        restored = advisor_review_queue_item_from_dict(advisor_review_queue_item_to_dict(item))
        self.assertEqual(item, restored)

    def test_35_single_item_summary_is_redacted(self):
        item = valid_item(
            suggestion_id="sug_secret",
            trigger_reason="api key sk-abc123 raw benchmark text answer key private user data",
            recommended_action="review only",
            notes=["Bearer abc.def secret password:=x"],
        )
        summary = summarize_advisor_review_queue_item(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "bearer abc.def", "password", "raw benchmark text", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_36_multi_item_summary_is_redacted_count_only(self):
        items = [valid_item(suggestion_id="sug_1"), valid_item(suggestion_id="sug_2", risk_level="medium")]
        summary = summarize_advisor_review_queue_items(items)
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        rendered = json.dumps(summary)
        self.assertNotIn("sug_1", rendered)
        self.assertNotIn("review prompt template coverage", rendered)

    def test_37_summary_does_not_contain_sensitive_strings(self):
        item = valid_item(
            suggestion_id="sug_api_key_token_secret",
            trigger_reason="api key token secret raw benchmark answer key official score private user data",
            recommended_action="operator review",
        )
        rendered = json.dumps(summarize_advisor_review_queue_item(item)).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data", "official score"]:
            self.assertNotIn(forbidden, rendered)

    def test_38_advisor_queue_adapter_design_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_adapter_design_v1.py"], cwd=str(ROOT), check=True)

    def test_39_advisor_prompt_template_library_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_prompt_template_library_v1.py"], cwd=str(ROOT), check=True)

    def test_40_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_41_no_forbidden_files_changed(self):
        changed = set(subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines())
        staged = set(subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines())
        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines())
        all_changed = changed | staged | untracked
        self.assertFalse(all_changed & FORBIDDEN_CHANGED)
        self.assertFalse(all_changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(all_changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
