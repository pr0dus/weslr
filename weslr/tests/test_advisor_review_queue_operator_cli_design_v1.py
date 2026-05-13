from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs" / "WESLR_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_DESIGN_V1.md"
REAL_QUEUE_FILE = ROOT / ".weslr" / "advisor_review_queue.jsonl"

ALLOWED_CHANGED = {
    "docs/WESLR_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_DESIGN_V1.md",
    "weslr/tests/test_advisor_review_queue_operator_cli_design_v1.py",
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


class AdvisorReviewQueueOperatorCliDesignV1Tests(unittest.TestCase):
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
        self.assert_doc_contains("Advisor Review Queue Operator CLI Design V1")

    def test_03_status_design_only(self):
        self.assert_doc_contains("design_only")

    def test_04_execution_disallowed(self):
        self.assert_doc_contains("execution_allowed = false")

    def test_05_no_official_score_claimed(self):
        self.assert_doc_contains("official_score_claimed = false")

    def test_06_no_queue_writes(self):
        self.assert_doc_contains("no_queue_writes")

    def test_07_no_external_model_calls(self):
        self.assert_doc_contains("no_external_model_calls")

    def test_08_mentions_operator_commands(self):
        for text in [
            "advisor-queue list",
            "advisor-queue show <id>",
            "advisor-queue summary",
            "advisor-queue decide <id>",
            "advisor-queue archive <id>",
            "advisor-queue export --redacted",
        ]:
            self.assert_doc_contains(text)

    def test_09_mentions_redacted_output_by_default(self):
        self.assert_doc_contains_lower("redacted output by default")

    def test_10_mentions_operator_approval_required(self):
        self.assert_doc_contains_lower("operator approval required")

    def test_11_mentions_append_only_status_update_events(self):
        self.assert_doc_contains_lower("append-only status update events")

    def test_12_forbids_external_model_calls(self):
        self.assert_doc_contains_lower("call external models")

    def test_13_forbids_advisor_provider_calls(self):
        self.assert_doc_contains_lower("call advisor providers")

    def test_14_forbids_automatic_implementation(self):
        self.assert_doc_contains_lower("implement suggestions automatically")

    def test_15_forbids_prompt_mutation(self):
        self.assert_doc_contains_lower("mutate prompts automatically")

    def test_16_forbids_provider_activation(self):
        self.assert_doc_contains_lower("activate providers")

    def test_17_forbids_runtime_config_changes(self):
        self.assert_doc_contains_lower("change runtime/config")

    def test_18_forbids_memory_mutation(self):
        self.assert_doc_contains_lower("mutate memory")

    def test_19_forbids_governance_override(self):
        self.assert_doc_contains_lower("override governance")

    def test_20_forbids_answer_selection(self):
        self.assert_doc_contains_lower("select answers")

    def test_21_forbids_truth_soundness_claim(self):
        self.assert_doc_contains_lower("claim truth/soundness")

    def test_22_forbids_official_score(self):
        self.assert_doc_contains_lower("claim official score")

    def test_23_forbids_raw_benchmark_text(self):
        self.assert_doc_contains_lower("store raw benchmark text")

    def test_24_forbids_secrets_api_keys_tokens(self):
        self.assert_doc_contains_lower("store secrets/api keys/tokens")

    def test_25_supports_institution_client_role_restrictions(self):
        self.assert_doc_contains_lower("institution deployments may restrict cli decisions by role")

    def test_26_supports_air_gapped_on_prem_local_queue(self):
        self.assert_doc_contains_lower("air-gapped/on-prem deployments keep queue local")

    def test_27_contains_future_phase_names(self):
        for text in [
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_SCHEMA_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_HELPERS_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_OPERATOR_CLI_COMMANDS_ONLY",
            "APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assert_doc_contains(text)

    def test_28_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")
        self.assertFalse(REAL_QUEUE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
