from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_DESIGN_V1.md",
    "weslr/tests/test_who_said_that_read_only_log_lookup_design_v1.py",
}


def doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


class WhoSaidThatReadOnlyLogLookupDesignV1Tests(unittest.TestCase):
    def test_01_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_02_contains_title(self):
        self.assertIn("Who Said That Read-Only Log Lookup Design V1", doc_text())

    def test_03_contains_design_only(self):
        self.assertIn("design_only", doc_text())

    def test_04_contains_execution_disabled(self):
        self.assertIn("execution_allowed = false", doc_text())

    def test_05_contains_no_official_score_claim(self):
        self.assertIn("official_score_claimed = false", doc_text())

    def test_06_contains_no_log_reads(self):
        self.assertIn("no_log_reads", doc_text())

    def test_07_contains_no_log_writes(self):
        self.assertIn("no_log_writes", doc_text())

    def test_08_contains_no_external_model_calls(self):
        self.assertIn("no_external_model_calls", doc_text())

    def test_09_contains_no_queue_writes(self):
        self.assertIn("no_queue_writes", doc_text())

    def test_10_documents_current_in_memory_chain(self):
        self.assertIn("provided in-memory records/events → parserless resolver → WhoSaidThatAnswer", doc_text())

    def test_11_documents_future_read_only_log_lookup_chain(self):
        self.assertIn("read-only attribution log lookup → selected VoiceAttributionLogEvent records → parserless resolver → WhoSaidThatAnswer", doc_text())

    def test_12_requires_explicit_path_policy(self):
        self.assertIn("require explicit path policy", doc_text())

    def test_13_never_creates_log_file(self):
        self.assertIn("never create the log file", doc_text())

    def test_14_never_writes_log_file(self):
        self.assertIn("never write to the log file", doc_text())

    def test_15_contains_lookup_modes(self):
        self.assertIn("Lookup Modes", doc_text())

    def test_16_contains_most_recent(self):
        self.assertIn("most_recent", doc_text())

    def test_17_contains_by_utterance_id(self):
        self.assertIn("by_utterance_id", doc_text())

    def test_18_contains_by_trace_ref(self):
        self.assertIn("by_trace_ref", doc_text())

    def test_19_contains_missing_log_behavior(self):
        self.assertIn("Missing-Log Behavior", doc_text())

    def test_20_missing_log_does_not_create_file(self):
        self.assertIn("do not create a log file", doc_text())

    def test_21_missing_log_does_not_infer_source(self):
        self.assertIn("do not infer source", doc_text())

    def test_22_contains_redaction_policy(self):
        self.assertIn("Redaction Policy", doc_text())

    def test_23_mentions_voice_attribution_log_event(self):
        self.assertIn("VoiceAttributionLogEvent", doc_text())

    def test_24_mentions_voice_source_attribution_record(self):
        self.assertIn("VoiceSourceAttributionRecord", doc_text())

    def test_25_mentions_who_said_that_query_intent(self):
        self.assertIn("WhoSaidThatQueryIntent", doc_text())

    def test_26_mentions_who_said_that_answer(self):
        self.assertIn("WhoSaidThatAnswer", doc_text())

    def test_27_mentions_parserless_resolver(self):
        self.assertIn("parserless resolver", doc_text())

    def test_28_forbids_log_writes(self):
        self.assertIn("log writes", doc_text())

    def test_29_forbids_log_creation(self):
        self.assertIn("log creation", doc_text())

    def test_30_forbids_queue_writes(self):
        self.assertIn("queue writes", doc_text())

    def test_31_forbids_registry_persistence(self):
        self.assertIn("registry persistence", doc_text())

    def test_32_forbids_runtime_chat_voice_wiring(self):
        self.assertIn("runtime/chat/voice wiring", doc_text())

    def test_33_forbids_model_advisor_calls(self):
        self.assertIn("model/advisor calls", doc_text())

    def test_34_forbids_provenance_guessing(self):
        self.assertIn("provenance guessing", doc_text())

    def test_35_forbids_unsupported_i_said_it_claims(self):
        self.assertIn("unsupported “I said it” claims", doc_text())

    def test_36_forbids_hidden_llm_provider_authority(self):
        self.assertIn("hidden LLM/provider authority", doc_text())

    def test_37_forbids_memory_mutation(self):
        self.assertIn("memory mutation", doc_text())

    def test_38_forbids_self_improvement_activation(self):
        self.assertIn("self-improvement activation", doc_text())

    def test_39_forbids_answer_selection(self):
        self.assertIn("answer selection", doc_text())

    def test_40_forbids_truth_soundness_authority(self):
        self.assertIn("truth/soundness authority", doc_text())

    def test_41_forbids_official_score(self):
        self.assertIn("official score", doc_text())

    def test_42_contains_future_phase_names(self):
        text = doc_text()
        for phase in [
            "APPROVE_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_SCHEMA_ONLY",
            "APPROVE_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_HELPERS_ONLY",
            "APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY",
            "APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY",
            "APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, text)

    def test_43_no_implementation_files_changed(self):
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        changed = set()
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            changed.add(path)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED_FILES), changed)


if __name__ == "__main__":
    unittest.main()
