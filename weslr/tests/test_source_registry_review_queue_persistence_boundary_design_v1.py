from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_BOUNDARY_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_BOUNDARY_DESIGN_V1.md",
    "weslr/tests/test_source_registry_review_queue_persistence_boundary_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/source_registry_review_queue_mapping.py",
    "weslr/advisor_review_queue_persistence.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/unregistered_source_detection.py",
    "weslr/provenance_source_registry.py",
    "weslr/provenance_source_registry_seed.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
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


class SourceRegistryReviewQueuePersistenceBoundaryDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""

    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_02_title_present(self):
        self.assertIn("Source Registry Review Queue Persistence Boundary Design V1", self.doc_text)

    def test_03_design_only(self):
        self.assertIn("design_only", self.doc_text)

    def test_04_execution_disabled(self):
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_05_official_score_false(self):
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_06_no_queue_writes(self):
        self.assertIn("no_queue_writes", self.doc_text)

    def test_07_no_registry_persistence(self):
        self.assertIn("no_registry_persistence", self.doc_text)

    def test_08_no_external_model_calls(self):
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_09_documents_current_in_memory_chain(self):
        self.assertIn("candidate metadata → UnregisteredSourceFinding → AdvisorReviewQueueItem proposal", self.doc_text)

    def test_10_documents_future_append_only_storage_chain(self):
        self.assertIn("AdvisorReviewQueueItem proposal → validated persistence event → append-only queue storage", self.doc_text)

    def test_11_persistence_never_automatic(self):
        self.assertIn("Persistence must never be automatic", self.doc_text)

    def test_12_requires_valid_unregistered_source_finding(self):
        self.assertIn("valid `UnregisteredSourceFinding`", self.doc_text)

    def test_13_requires_valid_advisor_review_queue_item(self):
        self.assertIn("valid `AdvisorReviewQueueItem`", self.doc_text)

    def test_14_requires_valid_persistence_event(self):
        self.assertIn("valid `AdvisorQueuePersistenceEvent`", self.doc_text)

    def test_15_requires_append_only_storage(self):
        self.assertIn("append-only storage", self.doc_text)

    def test_16_requires_redaction_before_write(self):
        self.assertIn("redaction before write", self.doc_text)

    def test_17_requires_operator_review(self):
        self.assertIn("operator-review required", self.doc_text)

    def test_18_requires_advisor_calls_disabled(self):
        self.assertIn("advisor calls disabled", self.doc_text)

    def test_19_forbids_source_auto_registration(self):
        self.assertIn("source auto-registration", self.doc_text)

    def test_20_forbids_source_activation(self):
        self.assertIn("source activation", self.doc_text)

    def test_21_forbids_self_improvement_activation(self):
        self.assertIn("self-improvement activation", self.doc_text)

    def test_22_forbids_prompt_mutation(self):
        self.assertIn("prompt mutation", self.doc_text)

    def test_23_forbids_provider_activation(self):
        self.assertIn("provider activation", self.doc_text)

    def test_24_forbids_runtime_config_mutation(self):
        self.assertIn("runtime/config mutation", self.doc_text)

    def test_25_forbids_memory_mutation(self):
        self.assertIn("memory mutation", self.doc_text)

    def test_26_forbids_advisor_model_call(self):
        self.assertIn("advisor/model call", self.doc_text)

    def test_27_forbids_queue_self_approval(self):
        self.assertIn("queue self-approval", self.doc_text)

    def test_28_forbids_truth_soundness_score_claim(self):
        self.assertIn("truth/soundness/score claim", self.doc_text)

    def test_29_says_dry_run_first(self):
        self.assertIn("Dry-run first", self.doc_text)
        self.assertIn("write nothing", self.doc_text)

    def test_30_tests_use_temp_paths_only(self):
        self.assertIn("Future tests may use temp paths only", self.doc_text)

    def test_31_real_queue_file_must_not_be_created_yet(self):
        self.assertIn("Real `.weslr/advisor_review_queue.jsonl` must not be created", self.doc_text)

    def test_32_supports_institution_client_policy(self):
        self.assertIn("Institution/client policy", self.doc_text)
        self.assertIn("local-only queue persistence", self.doc_text)
        self.assertIn("air-gapped/on-prem storage", self.doc_text)

    def test_33_contains_future_phase_names(self):
        for phrase in [
            "APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_DRY_RUN_HELPERS_ONLY",
            "APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_TEMP_PATH_HELPERS_ONLY",
            "APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_REAL_WRITE_POLICY_DESIGN_ONLY",
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_34_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
