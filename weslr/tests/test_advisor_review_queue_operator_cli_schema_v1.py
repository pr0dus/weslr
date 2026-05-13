from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.advisor_review_queue_cli import (  # noqa: E402
    ALLOWED_CLI_COMMANDS,
    AdvisorQueueCLIRequest,
    AdvisorQueueCLIResult,
    cli_request_from_dict,
    cli_request_to_dict,
    cli_result_from_dict,
    cli_result_to_dict,
    create_empty_cli_request,
    create_empty_cli_result,
    summarize_cli_result,
    validate_cli_request,
    validate_cli_result,
)

REAL_QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"
ALLOWED_CHANGED = {
    "weslr/advisor_review_queue_cli.py",
    "weslr/tests/test_advisor_review_queue_operator_cli_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_persistence.py",
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


def valid_request(**overrides):
    request = create_empty_cli_request(request_id="request_001", command="list")
    for key, value in overrides.items():
        setattr(request, key, value)
    return request


def valid_result(**overrides):
    result = create_empty_cli_result(request_id="request_001", command="list")
    for key, value in overrides.items():
        setattr(result, key, value)
    return result


class AdvisorReviewQueueOperatorCliSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(AdvisorQueueCLIRequest)
        self.assertTrue(AdvisorQueueCLIResult)
        self.assertTrue(create_empty_cli_request)
        self.assertTrue(create_empty_cli_result)

    def test_02_empty_request_instantiates(self):
        self.assertIsInstance(AdvisorQueueCLIRequest(), AdvisorQueueCLIRequest)

    def test_03_empty_result_instantiates(self):
        self.assertIsInstance(AdvisorQueueCLIResult(), AdvisorQueueCLIResult)

    def test_04_safe_request_defaults(self):
        request = valid_request()
        self.assertTrue(request.export_redacted)
        self.assertTrue(request.dry_run)
        self.assertTrue(request.requires_operator_approval)
        self.assertFalse(request.allow_queue_write)
        self.assertFalse(request.allow_external_model_call)
        self.assertFalse(request.allow_runtime_change)
        self.assertEqual([], validate_cli_request(request))

    def test_05_safe_result_defaults(self):
        result = valid_result()
        self.assertTrue(result.redacted)
        self.assertFalse(result.queue_file_written)
        self.assertFalse(result.external_model_call_made)
        self.assertFalse(result.runtime_change_made)
        self.assertFalse(result.answer_selection_made)
        self.assertFalse(result.truth_claim_made)
        self.assertFalse(result.official_score_claimed)
        self.assertEqual([], validate_cli_result(result))

    def test_06_all_commands_validate(self):
        for command in ALLOWED_CLI_COMMANDS:
            request = valid_request(command=command)
            if command in {"show", "archive"}:
                request.item_id = "item_001"
            if command == "decide":
                request.item_id = "item_001"
                request.operator_decision = "accepted"
            self.assertNotIn("invalid command", validate_cli_request(request))
            self.assertNotIn("invalid command", validate_cli_result(valid_result(command=command)))

    def test_07_invalid_command_fails(self):
        self.assertIn("invalid command", validate_cli_request(valid_request(command="bad")))
        self.assertIn("invalid command", validate_cli_result(valid_result(command="bad")))

    def test_08_missing_request_id_fails(self):
        self.assertIn("missing request id", validate_cli_request(valid_request(request_id="")))

    def test_09_invalid_limit_fails(self):
        for limit in [0, -1, 1001, "50"]:
            self.assertIn("invalid limit", validate_cli_request(valid_request(limit=limit)))

    def test_10_export_redacted_false_fails(self):
        self.assertIn("export_redacted must remain true", validate_cli_request(valid_request(export_redacted=False)))

    def test_11_dry_run_false_fails(self):
        self.assertIn("dry_run must remain true in schema-only phase", validate_cli_request(valid_request(dry_run=False)))

    def test_12_requires_operator_approval_false_fails(self):
        self.assertIn("requires_operator_approval must remain true", validate_cli_request(valid_request(requires_operator_approval=False)))

    def test_13_allow_queue_write_true_fails(self):
        self.assertIn("allow_queue_write must remain false", validate_cli_request(valid_request(allow_queue_write=True)))

    def test_14_allow_external_model_call_true_fails(self):
        self.assertIn("allow_external_model_call must remain false", validate_cli_request(valid_request(allow_external_model_call=True)))

    def test_15_allow_runtime_change_true_fails(self):
        self.assertIn("allow_runtime_change must remain false", validate_cli_request(valid_request(allow_runtime_change=True)))

    def test_16_decide_without_item_id_fails(self):
        self.assertIn("decide command requires item_id", validate_cli_request(valid_request(command="decide", operator_decision="accepted")))

    def test_17_decide_without_operator_decision_fails(self):
        self.assertIn("decide command requires operator_decision", validate_cli_request(valid_request(command="decide", item_id="item_001")))

    def test_18_show_without_item_id_fails(self):
        self.assertIn("show command requires item_id", validate_cli_request(valid_request(command="show")))

    def test_19_archive_without_item_id_fails(self):
        self.assertIn("archive command requires item_id", validate_cli_request(valid_request(command="archive")))

    def test_20_result_redacted_false_fails(self):
        self.assertIn("result must remain redacted", validate_cli_result(valid_result(redacted=False)))

    def test_21_result_queue_file_written_true_fails(self):
        self.assertIn("queue_file_written must remain false", validate_cli_result(valid_result(queue_file_written=True)))

    def test_22_result_external_model_call_made_true_fails(self):
        self.assertIn("external_model_call_made must remain false", validate_cli_result(valid_result(external_model_call_made=True)))

    def test_23_result_runtime_change_made_true_fails(self):
        self.assertIn("runtime_change_made must remain false", validate_cli_result(valid_result(runtime_change_made=True)))

    def test_24_result_answer_selection_made_true_fails(self):
        self.assertIn("answer_selection_made must remain false", validate_cli_result(valid_result(answer_selection_made=True)))

    def test_25_result_truth_claim_made_true_fails(self):
        self.assertIn("truth_claim_made must remain false", validate_cli_result(valid_result(truth_claim_made=True)))

    def test_26_result_official_score_claimed_true_fails(self):
        self.assertIn("official_score_claimed must remain false", validate_cli_result(valid_result(official_score_claimed=True)))

    def test_27_request_to_from_dict_roundtrip_works(self):
        request = valid_request(command="filter", filter_status="pending_review", filter_type="local_scan", filter_risk="medium")
        self.assertEqual(request, cli_request_from_dict(cli_request_to_dict(request)))

    def test_28_result_to_from_dict_roundtrip_works(self):
        result = valid_result(item_count=2, status_counts={"pending_review": 2}, risk_counts={"low": 1, "medium": 1})
        self.assertEqual(result, cli_result_from_dict(cli_result_to_dict(result)))

    def test_29_summary_is_redacted_count_only(self):
        summary = summarize_cli_result(valid_result(messages=["safe message"], errors=["safe error"], status_counts={"pending": 2}, risk_counts={"low": 1}))
        self.assertTrue(summary["redacted"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["message_count"])
        self.assertEqual(1, summary["error_count"])
        self.assertNotIn("messages", summary)
        self.assertNotIn("errors", summary)

    def test_30_summary_does_not_contain_sensitive_strings(self):
        result = valid_result(
            messages=["api key sk-abc123 token secret raw benchmark answer key private user data"],
            errors=["Bearer abc.def correct answer password:=bad"],
            status_counts={"pending": 1},
            risk_counts={"low": 1},
        )
        rendered = json.dumps(summarize_cli_result(result)).lower()
        for forbidden in ["api key", "sk-abc123", "token", "secret", "raw benchmark", "answer key", "private user data", "bearer abc.def", "correct answer", "password"]:
            self.assertNotIn(forbidden, rendered)
        errors = validate_cli_result(result)
        self.assertTrue(any("api key" in error.lower() for error in errors))
        self.assertTrue(any("token" in error.lower() for error in errors))
        self.assertTrue(any("secret" in error.lower() for error in errors))
        self.assertTrue(any("raw benchmark" in error.lower() for error in errors))
        self.assertTrue(any("answer key" in error.lower() for error in errors))
        self.assertTrue(any("private user data" in error.lower() for error in errors))

    def test_31_operator_cli_design_test_still_passes(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_operator_cli_design_v1.py"], cwd=str(ROOT), check=True)

    def test_32_persistence_helper_tests_still_pass(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_persistence_helpers_v1.py"], cwd=str(ROOT), check=True)

    def test_33_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_34_no_real_queue_file_created(self):
        self.assertFalse(REAL_QUEUE_FILE.exists())

    def test_35_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
