from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_VOICE_SOURCE_ATTRIBUTION_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_VOICE_SOURCE_ATTRIBUTION_DESIGN_V1.md",
    "weslr/tests/test_voice_source_attribution_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/source_registry_review_queue_mapping.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class VoiceSourceAttributionDesignV1Tests(unittest.TestCase):
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
        self.assertIn("Voice Source Attribution Design V1", self.doc_text)

    def test_03_design_only(self):
        self.assertIn("design_only", self.doc_text)

    def test_04_execution_disabled(self):
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_05_official_score_false(self):
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_06_no_runtime_integration(self):
        self.assertIn("no_runtime_integration", self.doc_text)

    def test_07_no_voice_wiring(self):
        self.assertIn("no_voice_wiring", self.doc_text)

    def test_08_no_external_model_calls(self):
        self.assertIn("no_external_model_calls", self.doc_text)

    def test_09_no_queue_writes(self):
        self.assertIn("no_queue_writes", self.doc_text)

    def test_10_contains_who_said_that(self):
        self.assertIn("who said that?", self.doc_text)

    def test_11_contains_was_llm_involved(self):
        self.assertIn("was an LLM involved?", self.doc_text)

    def test_12_contains_attribution_record_fields(self):
        self.assertIn("Attribution record fields", self.doc_text)

    def test_13_contains_utterance_id(self):
        self.assertIn("utterance_id", self.doc_text)

    def test_14_contains_output_provenance_id(self):
        self.assertIn("output_provenance_id", self.doc_text)

    def test_15_contains_source_subsystem(self):
        self.assertIn("source_subsystem", self.doc_text)

    def test_16_contains_model_provider(self):
        self.assertIn("model_provider", self.doc_text)

    def test_17_contains_model_name(self):
        self.assertIn("model_name", self.doc_text)

    def test_18_contains_llm_assisted(self):
        self.assertIn("llm_assisted", self.doc_text)

    def test_19_contains_trigger(self):
        self.assertIn("trigger", self.doc_text)

    def test_20_contains_authority_level(self):
        self.assertIn("authority_level", self.doc_text)

    def test_21_answers_from_provenance_records(self):
        self.assertIn("WESLR must answer from provenance records", self.doc_text)

    def test_22_must_not_guess_when_missing(self):
        self.assertIn("If provenance is missing, WESLR must not guess", self.doc_text)

    def test_23_every_future_voice_output_requires_attribution(self):
        self.assertIn("Every future voice/proactive output requires attribution", self.doc_text)

    def test_24_contains_llm_assisted_voice_rule(self):
        self.assertIn("LLM-assisted voice rule", self.doc_text)

    def test_25_contains_ambient_proactive_rule(self):
        self.assertIn("Ambient/proactive rule", self.doc_text)

    def test_26_contains_user_trust_rule(self):
        self.assertIn("User trust rule", self.doc_text)

    def test_27_mentions_output_provenance_envelope(self):
        self.assertIn("OutputProvenanceEnvelope", self.doc_text)

    def test_28_mentions_provenance_source_entry(self):
        self.assertIn("ProvenanceSourceEntry", self.doc_text)

    def test_29_contains_review_queue_integration(self):
        self.assertIn("Review queue integration", self.doc_text)

    def test_30_contains_self_improvement_relation(self):
        self.assertIn("Self-improvement relation", self.doc_text)

    def test_31_forbids_provenance_guessing(self):
        self.assertIn("provenance guessing", self.doc_text)

    def test_32_forbids_hidden_llm_authority(self):
        self.assertIn("hidden LLM authority", self.doc_text)

    def test_33_forbids_hidden_model_provider_involvement(self):
        self.assertIn("hidden model/provider involvement", self.doc_text)

    def test_34_forbids_unattributed_proactive_voice_output(self):
        self.assertIn("unattributed proactive/voice output", self.doc_text)

    def test_35_forbids_raw_sensitive_spoken_text_storage_by_default(self):
        self.assertIn("raw sensitive spoken text storage by default", self.doc_text)

    def test_36_forbids_memory_mutation_from_voice_attribution_alone(self):
        self.assertIn("memory mutation from voice attribution alone", self.doc_text)

    def test_37_forbids_runtime_chat_voice_wiring_in_this_phase(self):
        self.assertIn("runtime/chat/voice wiring in this phase", self.doc_text)

    def test_38_forbids_queue_writes_in_this_phase(self):
        self.assertIn("queue writes in this phase", self.doc_text)

    def test_39_forbids_self_improvement_activation(self):
        self.assertIn("self-improvement activation", self.doc_text)

    def test_40_forbids_answer_selection(self):
        self.assertIn("answer selection", self.doc_text)

    def test_41_forbids_truth_soundness_authority(self):
        self.assertIn("truth/soundness authority", self.doc_text)

    def test_42_forbids_official_score(self):
        self.assertIn("official score", self.doc_text)

    def test_43_contains_future_phase_names(self):
        for phrase in [
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_SCHEMA_ONLY",
            "APPROVE_VOICE_SOURCE_ATTRIBUTION_LOGGING_DESIGN_ONLY",
            "APPROVE_WHO_SAID_THAT_QUERY_SURFACE_DESIGN_ONLY",
            "APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY",
            "APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_44_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
