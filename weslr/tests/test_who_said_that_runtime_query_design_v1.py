from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_V1.md",
    "weslr/tests/test_who_said_that_runtime_query_design_v1.py",
}
FORBIDDEN_CHANGED_FILES = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "weslr/chat_responder.py",
    "weslr/runtime_chat.py",
    "weslr/pending_messages_queue.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/voice_source_attribution_log.py",
    "weslr/voice_source_attribution.py",
    "weslr/who_said_that_log_lookup.py",
    "weslr/who_said_that_query_surface.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


class WhoSaidThatRuntimeQueryDesignV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_02_contains_design_only_status(self):
        self.assertIn("design_only", doc_text())
        self.assertIn("runtime_query_design_only", doc_text())

    def test_03_contains_no_runtime_integration(self):
        self.assertIn("no_runtime_integration", doc_text())
        self.assertIn("no runtime integration", doc_text())

    def test_04_contains_no_chat_voice_wiring(self):
        text = doc_text()
        self.assertIn("no_chat_wiring", text)
        self.assertIn("no_voice_wiring", text)
        self.assertIn("no chat/voice wiring", text)

    def test_05_contains_who_said_that_question(self):
        self.assertIn("who said that?", doc_text())

    def test_06_contains_input_surfaces(self):
        text = doc_text()
        self.assertIn("chat", text)
        self.assertIn("voice", text)
        self.assertIn("terminal/operator CLI", text)

    def test_07_contains_future_routing_flow(self):
        text = doc_text()
        self.assertIn("detect attribution query intent", text)
        self.assertIn("WhoSaidThatQueryIntent", text)
        self.assertIn("approved read-only lookup layer", text)
        self.assertIn("parserless resolver", text)
        self.assertIn("WhoSaidThatAnswer", text)

    def test_08_contains_read_only_lookup_layer(self):
        self.assertIn("read-only lookup layer", doc_text())

    def test_09_contains_parserless_resolver(self):
        self.assertIn("parserless resolver", doc_text())

    def test_10_contains_missing_attribution_behavior(self):
        self.assertIn("Missing Attribution Behavior", doc_text())
        self.assertIn("attribution is missing or unknown", doc_text())

    def test_11_contains_no_guessing(self):
        self.assertIn("do not guess", doc_text())

    def test_12_contains_no_i_said_it_claim(self):
        self.assertIn("do not make an “I said it” claim", doc_text())

    def test_13_contains_llm_model_disclosure(self):
        text = doc_text()
        self.assertIn("LLM/model involvement", text)
        self.assertIn("disclose provider/model if recorded", text)
        self.assertIn("avoid hidden LLM authority", text)

    def test_14_contains_runtime_safety_boundaries(self):
        text = doc_text()
        self.assertIn("no answer selection", text)
        self.assertIn("no truth/soundness/score authority", text)
        self.assertIn("no memory mutation from query alone", text)
        self.assertIn("no queue writes in this phase", text)
        self.assertIn("no log writes", text)

    def test_15_contains_no_memory_mutation(self):
        self.assertIn("no_memory_mutation", doc_text())
        self.assertIn("no memory mutation", doc_text())

    def test_16_contains_no_log_writes(self):
        self.assertIn("no_log_writes", doc_text())
        self.assertIn("no log writes", doc_text())

    def test_17_contains_no_queue_writes(self):
        self.assertIn("no_queue_writes", doc_text())
        self.assertIn("no queue writes", doc_text())

    def test_18_contains_no_direct_voice_attribution_log_read_write(self):
        text = doc_text()
        self.assertIn("no direct log read", text)
        self.assertIn("no `.weslr/voice_source_attribution.jsonl` read or write", text)

    def test_19_contains_future_phase_names(self):
        text = doc_text()
        for phase in [
            "APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_SCHEMA_ONLY",
            "APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_HELPERS_ONLY",
            "APPROVE_WHO_SAID_THAT_CHAT_ROUTING_DESIGN_ONLY",
            "APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_RUNTIME_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, text)

    def test_20_no_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
