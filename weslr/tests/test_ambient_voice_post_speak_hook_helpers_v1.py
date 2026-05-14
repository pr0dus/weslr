from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ambient_voice_post_speak_hook import (  # noqa: E402
    create_blocked_post_speak_hook_result,
    create_failed_post_speak_hook_result,
    create_post_speak_hook_input_from_metadata,
    create_post_speak_hook_result_from_input,
    create_successful_post_speak_hook_result,
    summarize_post_speak_hook_result,
    summarize_post_speak_hook_results,
    validate_ambient_voice_post_speak_hook_input,
    validate_ambient_voice_post_speak_hook_result,
)

ALLOWED_CHANGED_FILES = {
    "weslr/ambient_voice_post_speak_hook.py",
    "weslr/tests/test_ambient_voice_post_speak_hook_helpers_v1.py",
}
FORBIDDEN_CHANGED_FILES = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def metadata(**overrides):
    data = {
        "input_id": "input_a",
        "hook_id": "hook_a",
        "pre_speak_result_id": "pre_result_a",
        "utterance_id": "utt_a",
        "output_provenance_id": "out_a",
        "attribution_record_id": "attr_a",
        "pre_speak_log_event_id": "pre_event_a",
        "source_subsystem": "ambient_loop",
        "tts_engine": "tts/local",
        "stt_engine": "stt/local",
        "speech_attempted": True,
        "speech_success": True,
        "speech_failed": False,
        "speech_blocked": False,
        "trace_refs": ["trace:a"],
    }
    data.update(overrides)
    return data


class AmbientVoicePostSpeakHookHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_module_imports(self):
        self.assertTrue(create_post_speak_hook_input_from_metadata)
        self.assertTrue(create_post_speak_hook_result_from_input)
        self.assertTrue(create_successful_post_speak_hook_result)
        self.assertTrue(create_failed_post_speak_hook_result)
        self.assertTrue(create_blocked_post_speak_hook_result)
        self.assertTrue(summarize_post_speak_hook_result)
        self.assertTrue(summarize_post_speak_hook_results)

    def test_02_valid_metadata_creates_input(self):
        item = create_post_speak_hook_input_from_metadata(**metadata())
        self.assertEqual("input_a", item.input_id)
        self.assertEqual("utt_a", item.utterance_id)
        self.assertEqual([], validate_ambient_voice_post_speak_hook_input(item))

    def test_03_successful_result_validates_with_attempted_success_provenance_attribution_trace_refs(self):
        result = create_successful_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            trace_refs=["trace:a"],
        )
        self.assertTrue(result.speech_attempted)
        self.assertTrue(result.speech_success)
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(result))

    def test_04_failure_result_validates_with_failure_reason(self):
        result = create_failed_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            failure_reason="tts_failed",
            trace_refs=["trace:a"],
        )
        self.assertTrue(result.speech_failed)
        self.assertTrue(result.no_ownership_claim_required)
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(result))

    def test_05_blocked_result_validates_with_failure_reason(self):
        result = create_blocked_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            failure_reason="pre_speak_blocked",
            trace_refs=["trace:a"],
        )
        self.assertTrue(result.speech_blocked)
        self.assertFalse(result.speech_attempted)
        self.assertEqual([], validate_ambient_voice_post_speak_hook_result(result))

    def test_06_success_without_attempted_fails(self):
        item = create_post_speak_hook_input_from_metadata(**metadata(speech_attempted=False, speech_success=True))
        result = create_post_speak_hook_result_from_input(item, result_id="result_a")
        self.assertIn("speech success without speech attempted", validate_ambient_voice_post_speak_hook_result(result))

    def test_07_success_without_trace_refs_fails(self):
        result = create_successful_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            trace_refs=[],
        )
        self.assertIn("speech success without trace refs", validate_ambient_voice_post_speak_hook_result(result))

    def test_08_failure_without_reason_fails(self):
        result = create_failed_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            failure_reason="",
            trace_refs=["trace:a"],
        )
        self.assertIn("speech failure without failure reason", validate_ambient_voice_post_speak_hook_result(result))

    def test_09_blocked_without_reason_fails(self):
        result = create_blocked_post_speak_hook_result(
            result_id="result_a",
            input_id="input_a",
            hook_id="hook_a",
            pre_speak_result_id="pre_result_a",
            utterance_id="utt_a",
            output_provenance_id="out_a",
            attribution_record_id="attr_a",
            failure_reason="",
            trace_refs=["trace:a"],
        )
        self.assertIn("speech blocked without failure reason", validate_ambient_voice_post_speak_hook_result(result))

    def test_10_no_ownership_rule_enforced_when_not_emitted(self):
        item = create_post_speak_hook_input_from_metadata(**metadata(speech_success=False, speech_failed=True, failure_reason="tts_failed", no_ownership_claim_required=False))
        result = create_post_speak_hook_result_from_input(item, result_id="result_a")
        self.assertIn("ownership claim allowed when speech was not emitted", validate_ambient_voice_post_speak_hook_result(result))

    def test_11_summaries_are_redacted_count_only(self):
        success = create_successful_post_speak_hook_result(result_id="success", input_id="input_a", hook_id="hook_a", pre_speak_result_id="pre", utterance_id="utt", output_provenance_id="out", attribution_record_id="attr", trace_refs=["trace:a"])
        failed = create_failed_post_speak_hook_result(result_id="failed", input_id="input_b", hook_id="hook_b", pre_speak_result_id="pre", utterance_id="utt_b", output_provenance_id="out", attribution_record_id="attr", failure_reason="tts_failed", trace_refs=["trace:b"])
        one = summarize_post_speak_hook_result(success)
        many = summarize_post_speak_hook_results([success, failed])
        self.assertEqual("redacted_count_only", one["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["result_count"])
        rendered = json.dumps({"one": one, "many": many}).lower()
        for forbidden in ["api key", "token", "secret", "raw spoken", "transcript", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_12_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_13_no_runtime_voice_wiring_or_side_effects(self):
        result = create_successful_post_speak_hook_result(result_id="result_a", input_id="input_a", hook_id="hook_a", pre_speak_result_id="pre", utterance_id="utt", output_provenance_id="out", attribution_record_id="attr", trace_refs=["trace:a"])
        summary = summarize_post_speak_hook_result(result)
        self.assertFalse(summary["runtime_voice_wiring_performed"])
        self.assertFalse(summary["log_write_performed"])
        self.assertFalse(summary["queue_write_performed"])
        self.assertFalse(summary["memory_mutation_performed"])
        self.assertFalse(summary["model_call_performed"])
        self.assertFalse(summary["speech_triggered"])

    def test_14_only_allowed_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
