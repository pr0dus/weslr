from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_UNREGISTERED_SOURCE_DETECTION_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_UNREGISTERED_SOURCE_DETECTION_DESIGN_V1.md",
    "weslr/tests/test_unregistered_source_detection_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/provenance_source_registry_seed.py",
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
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


class UnregisteredSourceDetectionDesignV1Tests(unittest.TestCase):
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
        self.assertIn("Unregistered Source Detection Design V1", self.doc_text)

    def test_03_design_only_status_present(self):
        self.assertIn("design_only", self.doc_text)

    def test_04_execution_disabled(self):
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_05_no_official_score_claim(self):
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_06_no_auto_registration_marker(self):
        self.assertIn("no_auto_registration", self.doc_text)

    def test_07_no_queue_writes_marker(self):
        self.assertIn("no_queue_writes", self.doc_text)

    def test_08_no_external_model_calls_marker(self):
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_09_identifies_modules_without_registry_entries(self):
        self.assertIn("identifies WESLR modules or artifacts", self.doc_text)
        self.assertIn("do not have provenance source registry entries", self.doc_text)

    def test_10_mentions_registry_seed(self):
        self.assertIn("in-memory provenance source registry seed", self.doc_text)

    def test_11_mentions_future_persisted_registry_entries(self):
        self.assertIn("future persisted registry entries", self.doc_text)

    def test_12_contains_detection_signals(self):
        self.assertIn("Detection signals", self.doc_text)
        for phrase in [
            "module name suggests output production",
            "functions that generate suggestions",
            "voice/proactive/ambient behavior",
            "advisor/review/queue behavior",
            "memory write behavior",
            "routing/decision behavior",
            "self-review/self-improvement behavior",
            "provenance envelope references unknown source",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_13_contains_unknown_source_policy(self):
        self.assertIn("Unknown-source policy", self.doc_text)

    def test_14_unknown_source_requires_operator_review(self):
        self.assertIn("require operator review", self.doc_text)

    def test_15_forbids_provenance_guessing(self):
        self.assertIn("do not guess provenance", self.doc_text)
        self.assertIn("no provenance guessing", self.doc_text)

    def test_16_forbids_auto_register(self):
        self.assertIn("do not auto-register", self.doc_text)
        self.assertIn("no auto-registration", self.doc_text)

    def test_17_forbids_auto_activate(self):
        self.assertIn("do not auto-activate", self.doc_text)
        self.assertIn("no auto-activate behavior", self.doc_text)

    def test_18_contains_future_finding_categories(self):
        for phrase in [
            "unregistered_source_candidate",
            "missing_source_registry_entry",
            "stale_source_registry_entry",
            "source_without_tests",
            "source_without_docs",
            "unknown_source_in_provenance",
            "source_authority_boundary_missing",
            "source_activation_policy_inconsistent",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_19_contains_unregistered_voice_or_proactive_source(self):
        self.assertIn("unregistered_voice_or_proactive_source", self.doc_text)

    def test_20_contains_unregistered_self_improvement_source(self):
        self.assertIn("unregistered_self_improvement_source", self.doc_text)

    def test_21_contains_review_queue_integration(self):
        self.assertIn("Review queue integration", self.doc_text)
        self.assertIn("local-scan and queue mapping helpers", self.doc_text)

    def test_22_this_phase_must_not_write_queues(self):
        self.assertIn("This phase must not write queues", self.doc_text)
        self.assertIn("no queue writes in this phase", self.doc_text)

    def test_23_contains_self_improvement_support(self):
        self.assertIn("Self-improvement support", self.doc_text)
        self.assertIn("WESLR-self-review-suggested", self.doc_text)
        self.assertIn("self-improvement-proposed", self.doc_text)

    def test_24_self_improvement_requires_registry_validation_tests_operator_approval(self):
        self.assertIn("Self-improvement modules require registry entry, validation, tests, and operator approval", self.doc_text)

    def test_25_contains_llm_advisor_integration(self):
        self.assertIn("LLM Advisor integration", self.doc_text)

    def test_26_advisor_output_non_authoritative_proposal_input(self):
        self.assertIn("Advisor output is non-authoritative proposal input", self.doc_text)

    def test_27_contains_institution_client_extension(self):
        self.assertIn("Institution/client extension", self.doc_text)
        self.assertIn("on-premise/air-gapped models", self.doc_text)
        self.assertIn("industrial adapters", self.doc_text)
        self.assertIn("private workflows", self.doc_text)

    def test_28_forbids_model_advisor_calls(self):
        self.assertIn("no model/advisor calls", self.doc_text)
        self.assertIn("no external model calls", self.doc_text)

    def test_29_forbids_runtime_chat_voice_wiring(self):
        self.assertIn("no runtime/chat/voice wiring", self.doc_text)

    def test_30_forbids_memory_mutation(self):
        self.assertIn("no memory mutation", self.doc_text)

    def test_31_forbids_daemon_cron_scheduler(self):
        self.assertIn("no daemon/cron/scheduler", self.doc_text)

    def test_32_forbids_answer_selection(self):
        self.assertIn("no answer selection", self.doc_text)

    def test_33_forbids_truth_soundness_authority(self):
        self.assertIn("no truth/soundness authority", self.doc_text)

    def test_34_forbids_official_score(self):
        self.assertIn("no official score", self.doc_text)

    def test_35_contains_future_phase_names(self):
        for phrase in [
            "APPROVE_UNREGISTERED_SOURCE_DETECTION_SCHEMA_ONLY",
            "APPROVE_UNREGISTERED_SOURCE_DETECTION_HELPERS_ONLY",
            "APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY",
            "APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_MAPPING_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_36_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
