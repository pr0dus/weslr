from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_VOICE_SOURCE_ATTRIBUTION_LOGGING_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_VOICE_SOURCE_ATTRIBUTION_LOGGING_DESIGN_V1.md",
    "weslr/tests/test_voice_source_attribution_logging_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_source_attribution.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/source_registry_review_queue_mapping.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class VoiceSourceAttributionLoggingDesignV1Tests(unittest.TestCase):
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

    def test_02_contains_title(self):
        self.assertIn("Voice Source Attribution Logging Design V1", self.doc_text)

    def test_03_contains_design_only(self):
        self.assertIn("design_only", self.doc_text)

    def test_04_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_05_contains_official_score_false(self):
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_06_contains_no_runtime_integration(self):
        self.assertIn("no_runtime_integration", self.doc_text)

    def test_07_contains_no_voice_wiring(self):
        self.assertIn("no_voice_wiring", self.doc_text)

    def test_08_contains_no_log_writes(self):
        self.assertIn("no_log_writes", self.doc_text)

    def test_09_contains_no_external_model_calls(self):
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_10_contains_no_queue_writes(self):
        self.assertIn("no_queue_writes", self.doc_text)

    def test_11_mentions_voice_source_attribution_record(self):
        self.assertIn("VoiceSourceAttributionRecord", self.doc_text)

    def test_12_mentions_output_provenance_envelope(self):
        self.assertIn("OutputProvenanceEnvelope", self.doc_text)

    def test_13_mentions_provenance_source_entry(self):
        self.assertIn("ProvenanceSourceEntry", self.doc_text)

    def test_14_contains_logging_lifecycle(self):
        self.assertIn("voice/proactive output candidate → output provenance envelope → voice attribution record → validation → append-only attribution log → later query surface", self.doc_text)

    def test_15_contains_pre_speak_attribution_draft(self):
        self.assertIn("Pre-speak attribution draft", self.doc_text)

    def test_16_contains_post_speak_attribution_confirmation(self):
        self.assertIn("Post-speak attribution confirmation", self.doc_text)

    def test_17_says_append_only_attribution_log(self):
        self.assertIn("append-only attribution log", self.doc_text)

    def test_18_says_raw_spoken_text_disabled_by_default(self):
        self.assertIn("raw spoken text disabled by default", self.doc_text)

    def test_19_mentions_future_path(self):
        self.assertIn(".weslr/voice_source_attribution.jsonl", self.doc_text)

    def test_20_says_do_not_create_this_file(self):
        self.assertIn("Do not create this file", self.doc_text)

    def test_21_contains_missing_attribution_handling(self):
        self.assertIn("Missing attribution handling", self.doc_text)

    def test_22_says_do_not_guess(self):
        self.assertIn("do not guess", self.doc_text)

    def test_23_says_no_i_said_it_without_provenance(self):
        self.assertIn("no claim “I said it” without provenance", self.doc_text)

    def test_24_contains_llm_model_disclosure(self):
        self.assertIn("LLM/model disclosure", self.doc_text)

    def test_25_contains_ambient_proactive_disclosure(self):
        self.assertIn("Ambient/proactive disclosure", self.doc_text)

    def test_26_who_said_that_depends_on_logged_records(self):
        self.assertIn("who said that?” query surface must depend on logged attribution records", self.doc_text)

    def test_27_contains_review_queue_integration(self):
        self.assertIn("Review queue integration", self.doc_text)

    def test_28_says_phase_must_not_write_queues(self):
        self.assertIn("This design phase must not write queues", self.doc_text)

    def test_29_supports_institution_client_policy(self):
        for phrase in ["local-only attribution log", "air-gapped storage", "admin-controlled retention policy", "role-restricted access"]:
            self.assertIn(phrase, self.doc_text)

    def test_30_forbids_provenance_guessing(self):
        self.assertIn("provenance guessing", self.doc_text)

    def test_31_forbids_hidden_llm_authority(self):
        self.assertIn("hidden LLM authority", self.doc_text)

    def test_32_forbids_hidden_model_provider_involvement(self):
        self.assertIn("hidden model/provider involvement", self.doc_text)

    def test_33_forbids_raw_spoken_text_storage_by_default(self):
        self.assertIn("raw spoken text storage by default", self.doc_text)

    def test_34_forbids_memory_mutation_from_attribution_alone(self):
        self.assertIn("memory mutation from attribution alone", self.doc_text)

    def test_35_forbids_log_writes_in_this_phase(self):
        self.assertIn("log writes in this phase", self.doc_text)

    def test_36_forbids_runtime_chat_voice_wiring_in_this_phase(self):
        self.assertIn("runtime/chat/voice wiring in this phase", self.doc_text)

    def test_37_forbids_self_improvement_activation(self):
        self.assertIn("self-improvement activation", self.doc_text)

    def test_38_forbids_answer_selection(self):
        self.assertIn("answer selection", self.doc_text)

    def test_39_forbids_truth_soundness_authority(self):
        self.assertIn("truth/soundness authority", self.doc_text)

    def test_40_forbids_official_score(self):
        self.assertIn("official score", self.doc_text)

    def test_41_contains_future_phase_names(self):
        for phrase in [
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_LOG_SCHEMA_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_LOGGING_HELPERS_ONLY",
            "APPROVE_WHO_SAID_THAT_QUERY_SURFACE_DESIGN_ONLY",
            "APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY",
            "APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_42_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
