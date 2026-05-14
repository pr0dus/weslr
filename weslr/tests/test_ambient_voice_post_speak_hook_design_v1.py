from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC_PATH = ROOT / "docs" / "WESLR_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_V1.md"
ALLOWED_CHANGED = {
    "docs/WESLR_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_V1.md",
    "weslr/tests/test_ambient_voice_post_speak_hook_design_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "weslr/ambient_voice_pre_speak_hook.py",
    "weslr/ambient_voice_provenance_wiring.py",
    "weslr/voice_source_attribution.py",
    "weslr/voice_source_attribution_log.py",
    "weslr/who_said_that_log_lookup.py",
    "weslr/who_said_that_query_surface.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


class AmbientVoicePostSpeakHookDesignV1Tests(unittest.TestCase):
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
        self.assertIn("no runtime integration in this phase", self.doc_text)

    def test_04_no_voice_wiring(self):
        self.assertIn("no_voice_wiring", self.doc_text)
        self.assertIn("no voice wiring in this phase", self.doc_text)

    def test_05_post_speak_confirmation_and_failure(self):
        self.assertIn("post-speak confirmation", self.doc_text)
        self.assertIn("post-speak hook", self.doc_text)
        self.assertIn("failed", self.doc_text)
        self.assertIn("blocked", self.doc_text)

    def test_06_required_output_records(self):
        self.assertIn("AmbientVoiceProvenanceHookRecord", self.doc_text)
        self.assertIn("VoiceAttributionLogEvent", self.doc_text)
        self.assertIn("confirmation/failure status", self.doc_text)

    def test_07_pre_speak_hook_result(self):
        self.assertIn("pre-speak hook result", self.doc_text)
        self.assertIn("speech emitted only if pre-speak allowed it", self.doc_text)

    def test_08_no_i_said_it_if_not_emitted(self):
        self.assertIn("no “I said it” claim if speech was not emitted", self.doc_text)

    def test_09_no_guessing(self):
        self.assertIn("no guessing", self.doc_text)
        self.assertIn("source unknown", self.doc_text)
        self.assertIn("operator review recommended", self.doc_text)

    def test_10_no_raw_spoken_text_by_default(self):
        self.assertIn("no raw spoken text by default", self.doc_text)

    def test_11_no_hidden_llm_authority(self):
        self.assertIn("no hidden LLM authority", self.doc_text)
        self.assertIn("no hidden provider/model authority", self.doc_text)

    def test_12_no_queue_or_log_writes(self):
        self.assertIn("no_queue_writes", self.doc_text)
        self.assertIn("no_log_writes", self.doc_text)
        self.assertIn("no queue writes in this phase", self.doc_text)
        self.assertIn("no log writes in this phase", self.doc_text)

    def test_13_no_side_effects_or_speech_triggered(self):
        for phrase in ["no_memory_mutation", "no model calls in this phase", "no advisor calls in this phase", "no config changes", "no speech triggered in this phase"]:
            self.assertIn(phrase, self.doc_text)

    def test_14_future_phase_names(self):
        for phrase in [
            "APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_SCHEMA_ONLY",
            "APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_HELPERS_ONLY",
            "APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(phrase, self.doc_text)

    def test_15_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_16_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
