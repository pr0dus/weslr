from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue_persistence import (  # noqa: E402
    ALLOWED_OPERATOR_DECISIONS,
    ALLOWED_PERSISTENCE_EVENT_TYPES,
    AdvisorQueuePersistenceEvent,
    AdvisorQueuePersistencePathPolicy,
    AdvisorQueuePersistenceSafetyFlags,
    create_empty_persistence_event,
    create_empty_persistence_path_policy,
    persistence_event_from_dict,
    persistence_event_to_dict,
    persistence_path_policy_from_dict,
    persistence_path_policy_to_dict,
    summarize_persistence_event,
    summarize_persistence_path_policy,
    validate_persistence_event,
    validate_persistence_path_policy,
)

ALLOWED_CHANGED = {
    "weslr/advisor_review_queue_persistence.py",
    "weslr/tests/test_advisor_review_queue_persistence_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/local_scan_advisor_review.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_discovery/review.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
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
    "review_queue.json",
    "export_queue.json",
    ".weslr/advisor_review_queue.jsonl",
}
QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"


def valid_event(**overrides):
    event = create_empty_persistence_event(
        event_id="event_001",
        event_type="queue_item_created",
        queue_item_id="queue_item_001",
        redacted_summary="redacted local scan queue item summary",
    )
    for key, value in overrides.items():
        setattr(event, key, value)
    return event


class AdvisorReviewQueuePersistenceSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(AdvisorQueuePersistenceSafetyFlags)
        self.assertTrue(AdvisorQueuePersistencePathPolicy)
        self.assertTrue(AdvisorQueuePersistenceEvent)

    def test_02_path_policy_instantiates(self):
        self.assertIsInstance(AdvisorQueuePersistencePathPolicy(), AdvisorQueuePersistencePathPolicy)

    def test_03_persistence_event_instantiates(self):
        self.assertIsInstance(AdvisorQueuePersistenceEvent(), AdvisorQueuePersistenceEvent)

    def test_04_safe_path_policy_defaults(self):
        policy = create_empty_persistence_path_policy()
        self.assertTrue(policy.append_only_required)
        self.assertTrue(policy.redaction_required)
        self.assertTrue(policy.operator_approval_required)
        self.assertFalse(policy.allow_absolute_paths)
        self.assertFalse(policy.allow_path_traversal)
        self.assertFalse(policy.allow_external_storage)

    def test_05_default_path_is_advisor_review_queue_jsonl(self):
        self.assertEqual(".weslr/advisor_review_queue.jsonl", create_empty_persistence_path_policy().queue_path)

    def test_06_storage_format_jsonl_validates(self):
        self.assertEqual([], validate_persistence_path_policy(create_empty_persistence_path_policy(storage_format="jsonl")))

    def test_07_invalid_storage_format_fails(self):
        self.assertIn("invalid storage_format", validate_persistence_path_policy(create_empty_persistence_path_policy(storage_format="sqlite")))

    def test_08_append_only_disabled_fails(self):
        self.assertIn("append_only_required must remain true", validate_persistence_path_policy(create_empty_persistence_path_policy(append_only_required=False)))

    def test_09_redaction_disabled_fails(self):
        self.assertIn("redaction_required must remain true", validate_persistence_path_policy(create_empty_persistence_path_policy(redaction_required=False)))

    def test_10_operator_approval_disabled_fails(self):
        self.assertIn("operator_approval_required must remain true", validate_persistence_path_policy(create_empty_persistence_path_policy(operator_approval_required=False)))

    def test_11_absolute_paths_allowed_fails(self):
        self.assertIn("absolute paths must remain disallowed", validate_persistence_path_policy(create_empty_persistence_path_policy(allow_absolute_paths=True)))

    def test_12_path_traversal_allowed_fails(self):
        self.assertIn("path traversal must remain disallowed", validate_persistence_path_policy(create_empty_persistence_path_policy(allow_path_traversal=True)))

    def test_13_external_storage_allowed_fails(self):
        self.assertIn("external storage must remain disallowed", validate_persistence_path_policy(create_empty_persistence_path_policy(allow_external_storage=True)))

    def test_14_all_event_types_validate(self):
        for event_type in ALLOWED_PERSISTENCE_EVENT_TYPES:
            event = valid_event(event_type=event_type)
            if event_type not in {"queue_item_created", "status_update_requested", "operator_decision_recorded", "queue_item_archived"}:
                event.queue_item_id = ""
            self.assertNotIn("invalid event_type", validate_persistence_event(event))

    def test_15_invalid_event_type_fails(self):
        self.assertIn("invalid event_type", validate_persistence_event(valid_event(event_type="bad")))

    def test_16_all_operator_decisions_validate(self):
        for decision in ALLOWED_OPERATOR_DECISIONS:
            self.assertNotIn("invalid operator_decision", validate_persistence_event(valid_event(operator_decision=decision)))

    def test_17_invalid_operator_decision_fails(self):
        self.assertIn("invalid operator_decision", validate_persistence_event(valid_event(operator_decision="bad")))

    def test_18_missing_event_id_fails(self):
        self.assertIn("missing event_id", validate_persistence_event(valid_event(event_id="")))

    def test_19_missing_queue_item_id_fails_for_queue_item_created_event(self):
        self.assertIn("missing queue_item_id", validate_persistence_event(valid_event(queue_item_id="")))

    def assert_flag_fails(self, field: str, expected: str):
        flags = AdvisorQueuePersistenceSafetyFlags(**{field: True})
        self.assertIn(expected, validate_persistence_event(valid_event(safety_flags=flags)))

    def test_20_queue_file_write_attempted_fails(self):
        self.assert_flag_fails("queue_file_write_attempted", "queue file write attempted")

    def test_21_queue_file_read_attempted_fails(self):
        self.assert_flag_fails("queue_file_read_attempted", "queue file read attempted")

    def test_22_database_write_attempted_fails(self):
        self.assert_flag_fails("database_write_attempted", "database write attempted")

    def test_23_external_model_call_attempted_fails(self):
        self.assert_flag_fails("external_model_call_attempted", "external model call attempted")

    def test_24_advisor_call_attempted_fails(self):
        self.assert_flag_fails("advisor_call_attempted", "advisor call attempted")

    def test_25_runtime_config_change_attempted_fails(self):
        self.assert_flag_fails("runtime_config_change_attempted", "runtime/config change attempted")

    def test_26_memory_mutation_attempted_fails(self):
        self.assert_flag_fails("memory_mutation_attempted", "memory mutation attempted")

    def test_27_governance_override_attempted_fails(self):
        self.assert_flag_fails("governance_override_attempted", "governance override attempted")

    def test_28_self_approval_attempted_fails(self):
        self.assert_flag_fails("self_approval_attempted", "self approval attempted")

    def test_29_raw_benchmark_text_included_fails(self):
        self.assert_flag_fails("raw_benchmark_text_included", "raw benchmark text included")

    def test_30_secrets_included_fails(self):
        self.assert_flag_fails("secrets_included", "secrets included")

    def test_31_private_user_data_included_fails(self):
        self.assert_flag_fails("private_user_data_included", "private user data included")

    def test_32_answer_selection_attempted_fails(self):
        self.assert_flag_fails("answer_selection_attempted", "answer selection attempted")

    def test_33_truth_authority_claimed_fails(self):
        self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")

    def test_34_soundness_authority_claimed_fails(self):
        self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_35_official_score_claimed_fails(self):
        self.assert_flag_fails("official_score_claimed", "official score claimed")

    def test_36_path_policy_to_from_dict_roundtrip_works(self):
        policy = create_empty_persistence_path_policy(retention_policy="manual_review")
        self.assertEqual(policy, persistence_path_policy_from_dict(persistence_path_policy_to_dict(policy)))

    def test_37_event_to_from_dict_roundtrip_works(self):
        event = valid_event(queue_item_snapshot={"suggestion_id": "safe_id"})
        self.assertEqual(event, persistence_event_from_dict(persistence_event_to_dict(event)))

    def test_38_path_policy_summary_is_redacted(self):
        summary = summarize_persistence_path_policy(create_empty_persistence_path_policy(retention_policy="api key token secret"))
        rendered = json.dumps(summary).lower()
        for forbidden in ["api key", "token", "secret"]:
            self.assertNotIn(forbidden, rendered)

    def test_39_event_summary_is_redacted(self):
        summary = summarize_persistence_event(valid_event(redacted_summary="api key token secret raw benchmark answer key private user data"))
        rendered = json.dumps(summary).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_40_summaries_do_not_contain_sensitive_strings(self):
        policy_summary = summarize_persistence_path_policy(create_empty_persistence_path_policy(retention_policy="sk-abc123 token secret"))
        event_summary = summarize_persistence_event(valid_event(queue_item_snapshot={"note": "Bearer abc.def raw benchmark text answer key private user data official score"}))
        rendered = json.dumps({"policy": policy_summary, "event": event_summary}).lower()
        for forbidden in ["sk-abc123", "bearer abc.def", "token", "secret", "raw benchmark", "answer key", "private user data", "official score"]:
            self.assertNotIn(forbidden, rendered)

    def test_41_advisor_queue_persistence_design_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_persistence_design_v1.py"], cwd=str(ROOT), check=True)

    def test_42_advisor_review_queue_schema_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_schema_v1.py"], cwd=str(ROOT), check=True)

    def test_43_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_44_no_queue_file_is_created(self):
        self.assertFalse(QUEUE_FILE.exists())

    def test_45_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
