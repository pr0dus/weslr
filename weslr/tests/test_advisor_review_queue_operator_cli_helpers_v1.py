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
    AdvisorQueueCLIRequest,
    AdvisorQueueCLIResult,
    create_cli_request_from_operator_intent,
    create_cli_result_for_request,
    summarize_cli_requests,
    summarize_cli_results,
    validate_cli_request,
    validate_cli_result,
    validate_operator_decision_for_cli,
)

REAL_QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"
ALLOWED_CHANGED = {
    "weslr/advisor_review_queue_cli.py",
    "weslr/tests/test_advisor_review_queue_operator_cli_helpers_v1.py",
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


class AdvisorReviewQueueOperatorCliHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def make_request(self, command="list", **overrides):
        data = {"command": command, "request_id": "request_001"}
        data.update(overrides)
        return create_cli_request_from_operator_intent(**data)

    def test_01_module_imports(self):
        self.assertTrue(AdvisorQueueCLIRequest)
        self.assertTrue(AdvisorQueueCLIResult)
        self.assertTrue(create_cli_request_from_operator_intent)
        self.assertTrue(create_cli_result_for_request)
        self.assertTrue(summarize_cli_requests)
        self.assertTrue(summarize_cli_results)
        self.assertTrue(validate_operator_decision_for_cli)

    def test_02_create_list_request_from_operator_intent(self):
        request = self.make_request("list")
        self.assertEqual("list", request.command)
        self.assertEqual([], validate_cli_request(request))

    def test_03_create_show_request_with_item_id(self):
        request = self.make_request("show", item_id="item_001")
        self.assertEqual("item_001", request.item_id)

    def test_04_show_request_without_item_id_fails(self):
        with self.assertRaises(ValueError):
            self.make_request("show")

    def test_05_create_decide_request_with_operator_decision(self):
        request = self.make_request("decide", item_id="item_001", operator_decision="accepted")
        self.assertEqual("accepted", request.operator_decision)
        self.assertEqual([], validate_operator_decision_for_cli(request.operator_decision))

    def test_06_decide_request_without_item_id_fails(self):
        with self.assertRaises(ValueError):
            self.make_request("decide", operator_decision="accepted")

    def test_07_decide_request_without_decision_fails(self):
        with self.assertRaises(ValueError):
            self.make_request("decide", item_id="item_001")

    def test_08_create_archive_request_with_item_id(self):
        request = self.make_request("archive", item_id="item_001")
        self.assertEqual("archive", request.command)

    def test_09_create_summary_request(self):
        request = self.make_request("summary")
        self.assertEqual("summary", request.command)

    def test_10_request_defaults_remain_dry_run(self):
        self.assertTrue(self.make_request().dry_run)

    def test_11_request_defaults_require_operator_approval(self):
        self.assertTrue(self.make_request().requires_operator_approval)

    def test_12_request_defaults_do_not_allow_queue_write(self):
        self.assertFalse(self.make_request().allow_queue_write)

    def test_13_request_defaults_do_not_allow_model_call(self):
        self.assertFalse(self.make_request().allow_external_model_call)

    def test_14_request_defaults_do_not_allow_runtime_change(self):
        self.assertFalse(self.make_request().allow_runtime_change)

    def test_15_create_result_for_request(self):
        result = create_cli_result_for_request(self.make_request(), success=True, item_count=2)
        self.assertEqual("request_001", result.request_id)
        self.assertEqual(2, result.item_count)
        self.assertEqual([], validate_cli_result(result))

    def test_16_result_remains_redacted(self):
        self.assertTrue(create_cli_result_for_request(self.make_request()).redacted)

    def test_17_result_does_not_mark_queue_file_written(self):
        self.assertFalse(create_cli_result_for_request(self.make_request()).queue_file_written)

    def test_18_result_does_not_mark_model_call_made(self):
        self.assertFalse(create_cli_result_for_request(self.make_request()).external_model_call_made)

    def test_19_result_does_not_mark_runtime_change_made(self):
        self.assertFalse(create_cli_result_for_request(self.make_request()).runtime_change_made)

    def test_20_summarize_requests_is_redacted_count_only(self):
        summary = summarize_cli_requests([self.make_request("list"), self.make_request("summary", request_id="request_002")])
        self.assertTrue(summary["redacted"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(2, summary["request_count"])
        self.assertEqual(1, summary["command_counts"]["list"])
        self.assertNotIn("item_id", summary)

    def test_21_summarize_results_is_redacted_count_only(self):
        result = create_cli_result_for_request(self.make_request(), messages=["safe"], errors=["safe error"])
        summary = summarize_cli_results([result])
        self.assertTrue(summary["redacted"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual(1, summary["result_count"])
        self.assertEqual(1, summary["message_count"])
        self.assertEqual(1, summary["error_count"])
        self.assertNotIn("messages", summary)
        self.assertNotIn("errors", summary)

    def test_22_summaries_do_not_contain_sensitive_strings(self):
        unsafe_request = AdvisorQueueCLIRequest(
            request_id="request_unsafe",
            command="list",
            filter_status="api key sk-abc123 token secret raw benchmark answer key private user data",
        )
        unsafe_result = AdvisorQueueCLIResult(
            request_id="request_unsafe",
            command="list",
            messages=["Bearer abc.def correct answer password:=bad private user data"],
        )
        rendered = json.dumps({"requests": summarize_cli_requests([unsafe_request]), "results": summarize_cli_results([unsafe_result])}).lower()
        for forbidden in ["api key", "sk-abc123", "token", "secret", "raw benchmark", "answer key", "private user data", "bearer abc.def", "correct answer", "password"]:
            self.assertNotIn(forbidden, rendered)

    def test_23_no_real_queue_file_created(self):
        self.assertFalse(REAL_QUEUE_FILE.exists())

    def test_24_no_external_model_calls(self):
        summary = summarize_cli_results([create_cli_result_for_request(self.make_request())])
        self.assertFalse(summary["external_model_call_made"])

    def test_25_no_runtime_config_changes(self):
        summary = summarize_cli_requests([self.make_request()])
        self.assertFalse(summary["runtime_change_made"])

    def test_26_no_answer_selection(self):
        summary = summarize_cli_results([create_cli_result_for_request(self.make_request())])
        self.assertFalse(summary["answer_selection_made"])

    def test_27_no_truth_soundness_claim(self):
        summary = summarize_cli_results([create_cli_result_for_request(self.make_request())])
        self.assertFalse(summary["truth_claim_made"])

    def test_28_no_official_score(self):
        summary = summarize_cli_results([create_cli_result_for_request(self.make_request())])
        self.assertFalse(summary["official_score_claimed"])

    def test_29_schema_tests_still_pass(self):
        subprocess.run(["python3", "weslr/tests/test_advisor_review_queue_operator_cli_schema_v1.py"], cwd=str(ROOT), check=True)

    def test_30_release_gate_check_pass(self):
        subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), check=True)

    def test_31_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
