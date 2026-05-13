from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs" / "WESLR_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_DESIGN_V1.md"
REAL_QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"

ALLOWED_CHANGED = {
    "docs/WESLR_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_DESIGN_V1.md",
    "weslr/tests/test_advisor_review_queue_operator_cli_commands_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/advisor_review_queue_cli.py",
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


class AdvisorReviewQueueOperatorCliCommandsDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def assert_doc_contains(self, text: str):
        self.assertIn(text, self.doc)

    def assert_doc_contains_lower(self, text: str):
        self.assertIn(text.lower(), self.doc_lower)

    def test_01_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_02_title_present(self):
        self.assert_doc_contains("Advisor Review Queue Operator CLI Commands Design V1")

    def test_03_status_design_only(self):
        self.assert_doc_contains("design_only")

    def test_04_execution_disallowed(self):
        self.assert_doc_contains("execution_allowed = false")

    def test_05_no_official_score_claimed(self):
        self.assert_doc_contains("official_score_claimed = false")

    def test_06_no_command_registration(self):
        self.assert_doc_contains("no_command_registration")

    def test_07_no_queue_writes(self):
        self.assert_doc_contains("no_queue_writes")

    def test_08_no_external_model_calls(self):
        self.assert_doc_contains("no_external_model_calls")

    def test_09_mentions_all_future_commands(self):
        for text in [
            "advisor-queue list",
            "advisor-queue show <id>",
            "advisor-queue summary",
            "advisor-queue filter --status --type --risk",
            "advisor-queue decide <id> --decision accepted|rejected|deferred",
            "advisor-queue archive <id>",
            "advisor-queue export --redacted",
        ]:
            self.assert_doc_contains(text)

    def test_10_thin_shells_over_validated_helpers(self):
        self.assert_doc_contains_lower("thin shells over validated helper functions")

    def test_11_commands_create_cli_request(self):
        self.assert_doc_contains("AdvisorQueueCLIRequest")

    def test_12_commands_return_cli_result(self):
        self.assert_doc_contains("AdvisorQueueCLIResult")

    def test_13_redacted_output_by_default(self):
        self.assert_doc_contains_lower("redacted summaries by default")
        self.assert_doc_contains_lower("redacted by default")

    def test_14_dry_run_no_io_first(self):
        self.assert_doc_contains_lower("dry-run/no-i/o first")

    def test_15_no_default_write_to_real_queue(self):
        self.assert_doc_contains("no default write to `.weslr/advisor_review_queue.jsonl`")

    def test_16_real_queue_read_write_requires_separate_approval(self):
        self.assert_doc_contains_lower("real queue read/write must require a separate phase")

    def test_17_forbids_external_model_calls(self):
        self.assert_doc_contains_lower("no external model calls")

    def test_18_forbids_advisor_provider_calls(self):
        self.assert_doc_contains_lower("no advisor provider calls")

    def test_19_forbids_automatic_implementation(self):
        self.assert_doc_contains_lower("no automatic implementation")

    def test_20_forbids_prompt_mutation(self):
        self.assert_doc_contains_lower("no prompt mutation")

    def test_21_forbids_provider_activation(self):
        self.assert_doc_contains_lower("no provider activation")

    def test_22_forbids_runtime_config_changes(self):
        self.assert_doc_contains_lower("no runtime/config changes")

    def test_23_forbids_memory_mutation(self):
        self.assert_doc_contains_lower("no memory mutation")

    def test_24_forbids_governance_override(self):
        self.assert_doc_contains_lower("no governance override")

    def test_25_forbids_answer_selection(self):
        self.assert_doc_contains_lower("no answer selection")

    def test_26_forbids_truth_soundness_claim(self):
        self.assert_doc_contains_lower("no truth/soundness claim")

    def test_27_forbids_official_score(self):
        self.assert_doc_contains_lower("no official score")

    def test_28_forbids_raw_benchmark_text(self):
        self.assert_doc_contains_lower("no raw benchmark text")

    def test_29_forbids_secrets_api_keys_tokens(self):
        self.assert_doc_contains_lower("no secrets/api keys/tokens")

    def test_30_supports_institution_client_role_restrictions(self):
        self.assert_doc_contains_lower("institution deployments may restrict commands by role")

    def test_31_supports_air_gapped_on_prem_local_queue(self):
        self.assert_doc_contains_lower("air-gapped/on-prem deployments keep queue local")

    def test_32_contains_future_phase_names(self):
        for text in [
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_DRY_RUN_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_READ_ONLY_COMMANDS_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_STATUS_UPDATE_COMMANDS_ONLY",
            "APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assert_doc_contains(text)

    def test_33_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")
        self.assertFalse(REAL_QUEUE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
