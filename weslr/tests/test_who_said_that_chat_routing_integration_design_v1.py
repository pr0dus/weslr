from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_WHO_SAID_THAT_CHAT_ROUTING_INTEGRATION_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_WHO_SAID_THAT_CHAT_ROUTING_INTEGRATION_DESIGN_V1.md",
    "weslr/tests/test_who_said_that_chat_routing_integration_design_v1.py",
}
FORBIDDEN_CHANGED_FILES = {
    "weslr/chat_responder.py",
    "weslr/runtime_chat.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "weslr/pending_messages_queue.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/voice_source_attribution_log.py",
    "weslr/voice_source_attribution.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


class WhoSaidThatChatRoutingIntegrationDesignV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_02_contains_design_only_status(self):
        text = doc_text()
        self.assertIn("design_only", text)
        self.assertIn("chat_routing_integration_design_only", text)

    def test_03_contains_no_runtime_integration(self):
        text = doc_text()
        self.assertIn("no_runtime_integration", text)
        self.assertIn("no runtime integration", text)

    def test_04_contains_no_chat_responder_changes(self):
        text = doc_text()
        self.assertIn("no_chat_responder_changes", text)
        self.assertIn("no chat responder changes", text)

    def test_05_contains_current_stack(self):
        text = doc_text()
        self.assertIn("chat routing helpers", text)
        self.assertIn("runtime query helpers", text)
        self.assertIn("read-only lookup helpers", text)
        self.assertIn("parserless resolver", text)
        self.assertIn("attribution answer schemas", text)

    def test_06_contains_future_integration_point(self):
        text = doc_text()
        self.assertIn("Future Integration Point", text)
        self.assertIn("detect attribution intent", text)
        self.assertIn("who-said-that path", text)

    def test_07_contains_fallthrough_to_normal_chat(self):
        text = doc_text()
        self.assertIn("fall through to normal chat", text)
        self.assertIn("Fallthrough to Normal Chat", text)
        self.assertIn("fallthrough to normal chat", text)

    def test_08_contains_missing_attribution_behavior(self):
        text = doc_text()
        self.assertIn("Missing Attribution Behavior", text)
        self.assertIn("say attribution missing/unknown", text)

    def test_09_contains_no_guessing(self):
        self.assertIn("no guessing", doc_text())

    def test_10_contains_no_i_said_it_claim(self):
        self.assertIn("no “I said it” claim", doc_text())

    def test_11_contains_no_log_writes(self):
        text = doc_text()
        self.assertIn("no_log_writes", text)
        self.assertIn("log reads/writes in this phase", text)

    def test_12_contains_no_queue_writes(self):
        text = doc_text()
        self.assertIn("no_queue_writes", text)
        self.assertIn("queue writes", text)

    def test_13_contains_no_model_calls(self):
        text = doc_text()
        self.assertIn("no_model_calls", text)
        self.assertIn("model calls", text)

    def test_14_contains_no_memory_mutation(self):
        text = doc_text()
        self.assertIn("no_memory_mutation", text)
        self.assertIn("memory mutation", text)

    def test_15_contains_truth_soundness_score_boundary(self):
        text = doc_text()
        self.assertIn("truth/soundness/score claims", text)
        self.assertIn("official score claims", text)

    def test_16_contains_future_phase_names(self):
        text = doc_text()
        for phase in [
            "APPROVE_WHO_SAID_THAT_CHAT_ROUTING_INTEGRATION_HELPERS_ONLY",
            "APPROVE_WHO_SAID_THAT_CHAT_ROUTING_DRY_RUN_ONLY",
            "APPROVE_WHO_SAID_THAT_CHAT_ROUTING_RUNTIME_WIRING_DESIGN_ONLY",
            "APPROVE_WHO_SAID_THAT_VOICE_ROUTING_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phase, text)

    def test_17_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")

    def test_18_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
