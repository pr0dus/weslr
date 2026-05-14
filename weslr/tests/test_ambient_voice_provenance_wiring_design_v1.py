from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_V1.md",
    "weslr/tests/test_ambient_voice_provenance_wiring_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "weslr/voice_source_attribution.py",
    "weslr/voice_source_attribution_log.py",
    "weslr/who_said_that_log_lookup.py",
    "weslr/who_said_that_query_surface.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


class AmbientVoiceProvenanceWiringDesignV1Tests(unittest.TestCase):
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

    def test_02_design_only_status(self):
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)

    def test_03_no_runtime_integration(self):
        self.assertIn("no_runtime_integration", self.doc_text)
        self.assertIn("runtime integration in this phase", self.doc_text)

    def test_04_no_voice_wiring(self):
        self.assertIn("no_voice_wiring", self.doc_text)
        self.assertIn("voice gateway changes", self.doc_text)

    def test_05_no_log_writes(self):
        self.assertIn("no_log_writes", self.doc_text)
        self.assertIn("log writes in this phase", self.doc_text)

    def test_06_no_queue_writes(self):
        self.assertIn("no_queue_writes", self.doc_text)
        self.assertIn("queue writes in this phase", self.doc_text)

    def test_07_no_model_calls(self):
        self.assertIn("no_model_calls", self.doc_text)
        self.assertIn("no_external_model_calls", self.doc_text)
        self.assertIn("model calls in this phase", self.doc_text)

    def test_08_no_memory_mutation(self):
        self.assertIn("no_memory_mutation", self.doc_text)
        self.assertIn("memory mutation", self.doc_text)

    def test_09_current_safe_stack(self):
        for phrase in [
            "VoiceSourceAttributionRecord",
            "VoiceAttributionLogEvent",
            "Logging helpers",
            "Who-said-that query helpers",
            "Parserless resolver",
            "Read-only lookup helpers",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_10_future_wiring_points(self):
        for phrase in [
            "voice gateway",
            "ambient loop",
            "proactive suggestions",
            "TTS emission",
            "STT transcript path",
            "local response generation",
            "model-assisted response generation",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_11_pre_speak_and_post_speak_attribution(self):
        self.assertIn("Pre-speak attribution draft", self.doc_text)
        self.assertIn("Post-speak attribution confirmation/failure", self.doc_text)
        self.assertIn("append-only attribution log", self.doc_text)
        self.assertIn("future who-said-that lookup", self.doc_text)

    def test_12_missing_attribution_rule(self):
        for phrase in ["no guessing", "no “I said it” claim", "source unknown", "operator review recommended"]:
            self.assertIn(phrase, self.doc_text)

    def test_13_llm_model_assisted_rule(self):
        for phrase in [
            "provider/model recorded when available",
            "no hidden LLM authority",
            "no hidden model/provider involvement",
            "no claim of independent WESLR understanding without non-LLM provenance",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_14_no_truth_or_score_claims(self):
        self.assertIn("truth/soundness claims", self.doc_text)
        self.assertIn("official score claims", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_15_future_phase_names(self):
        for phrase in [
            "APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_SCHEMA_ONLY",
            "APPROVE_AMBIENT_VOICE_PRE_SPEAK_HOOK_DESIGN_ONLY",
            "APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_ONLY",
            "APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_16_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_17_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
