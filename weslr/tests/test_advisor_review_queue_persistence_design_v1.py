from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_ADVISOR_REVIEW_QUEUE_PERSISTENCE_DESIGN_V1.md",
    "weslr/tests/test_advisor_review_queue_persistence_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/local_scan_advisor_review.py",
    "weslr/advisor_review_queue.py",
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


class AdvisorReviewQueuePersistenceDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.doc_lower = cls.doc_text.lower()

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_02_title_present(self):
        self.assertIn("Advisor Review Queue Persistence Design V1", self.doc_text)

    def test_03_design_only_present(self):
        self.assertIn("design_only", self.doc_text)

    def test_04_execution_allowed_false_present(self):
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_05_official_score_claimed_false_present(self):
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_06_no_queue_writes_present(self):
        self.assertIn("no_queue_writes", self.doc_text)

    def test_07_no_external_model_calls_present(self):
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_08_mentions_advisor_review_queue_item(self):
        self.assertIn("AdvisorReviewQueueItem", self.doc_text)

    def test_09_mentions_jsonl_or_json_queue(self):
        self.assertTrue("jsonl" in self.doc_lower or "json queue" in self.doc_lower)

    def test_10_says_append_only_event_log(self):
        self.assertIn("append-only event log", self.doc_lower)

    def test_11_says_records_validated_before_persistence(self):
        self.assertIn("all records are validated before persistence", self.doc_lower)

    def test_12_says_redacted_summaries_only(self):
        self.assertIn("redacted summaries only", self.doc_lower)

    def test_13_forbids_raw_benchmark_text(self):
        self.assertIn("no raw benchmark text", self.doc_lower)

    def test_14_forbids_secrets_api_keys_tokens(self):
        for phrase in ["no secrets", "api keys", "tokens"]:
            self.assertIn(phrase, self.doc_lower)

    def test_15_forbids_private_user_data_by_default(self):
        self.assertIn("no private user data by default", self.doc_lower)

    def test_16_forbids_external_model_calls(self):
        self.assertIn("no external model calls", self.doc_lower)

    def test_17_forbids_advisor_calls(self):
        self.assertIn("no advisor calls", self.doc_lower)

    def test_18_forbids_automatic_implementation(self):
        self.assertIn("no automatic implementation", self.doc_lower)

    def test_19_forbids_prompt_mutation(self):
        self.assertIn("no prompt mutation", self.doc_lower)

    def test_20_forbids_provider_activation(self):
        self.assertIn("no provider activation", self.doc_lower)

    def test_21_forbids_runtime_config_changes(self):
        self.assertIn("no runtime/config changes", self.doc_lower)

    def test_22_forbids_memory_mutation(self):
        self.assertIn("no memory mutation", self.doc_lower)

    def test_23_forbids_governance_override(self):
        self.assertIn("no governance override", self.doc_lower)

    def test_24_forbids_answer_selection(self):
        self.assertIn("no answer selection", self.doc_lower)

    def test_25_forbids_truth_soundness_claim(self):
        self.assertIn("no truth/soundness claim", self.doc_lower)

    def test_26_forbids_official_score(self):
        self.assertIn("no official score", self.doc_lower)

    def test_27_supports_institution_client_storage_policy(self):
        self.assertIn("institutions may choose storage location and policy later", self.doc_lower)
        self.assertIn("client deployment policy", self.doc_lower)

    def test_28_supports_air_gapped_on_prem_local_only_storage(self):
        self.assertIn("air-gapped/on-prem deployments can keep the queue local only", self.doc_lower)

    def test_29_contains_future_phase_names(self):
        for phase in [
            "APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_SCHEMA_ONLY",
            "APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_HELPERS_ONLY",
            "APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY",
            "APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY",
            "APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, self.doc_text)

    def test_30_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
